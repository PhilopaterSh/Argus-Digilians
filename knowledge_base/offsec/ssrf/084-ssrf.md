# SSRF — h1

- source: h1
- class: ssrf
- cwe: CWE-918
- severity: high
- program: gitlab
- quality_score: 13

## Scenario

Analyze the following vulnerability report and provide a structured security assessment.

**Report Title:** SSRF on project import via the remote_attachment_url on a Note
**Affected Asset:** gitlab.com

**Vulnerability Description:**
### Summary

The Note model has an `attachment` which is provided by a CarrierWave uploader:

```ruby
mount_uploader :attachment, AttachmentUploader
```

One of the features this provides is the ability to download and attach a file via a url, see https://github.com/carrierwaveuploader/carrierwave/blob/v1.3.1/lib/carrierwave/mount.rb#L80. This means that the Note model has a method `remote_attachment_url=` which can be used to perform this action.

As this attribute isn't removed by the `AttributeCleaner` on project import, it can be set in the `project.json` for a note and will be set when the note is created, downloading the file:

https://github.com/carrierwaveuploader/carrierwave/blob/v1.3.1/lib/carrierwave/mounter.rb#L72
```ruby
  def remote_urls=(urls)
      return if not urls or urls == "" or urls.all?(&:blank?)

      @remote_urls = urls
      @download_error = nil
      @integrity_error = nil

      @uploaders = urls.zip(remote_request_headers || []).map do |url, header|
        uploader = blank_uploader
        uploader.download!(url, header || {})
        uploader
      end
```

https://github.com/carrierwaveuploader/carrierwave/blob/v1.3.1/lib/carrierwave/uploader/download.rb#L43
```ruby
    def file
          if @file.blank?
            headers = @remote_headers.
              reverse_merge('User-Agent' => "CarrierWave/#{CarrierWave::VERSION}")

            @file = Kernel.open(@uri.to_s, headers)
            @file = @file.is_a?(String) ? StringIO.new(@file) : @file
          end
```

The downloaded file is then attached to the note and can be viewed from the newly imported project.

Any model that has a `mount_uploader` and is importable is potentially vulnerable to the same attack, although the majority of the others are `AvatarUploader` which checks the file type and prevents the response from being viewed.

### Steps to reproduce

1. Create a new project
1. Create an issue in the project
1. Add a note to the issue
1. Export the project
1. Extract the export
1. Add  `remote_attachment_url` to the `note` hash with a url
1. Recompress the export and import it
1. View the note on the issue

Demo {F756257}

### Examples

Example of project import on gitlab.com hitting postbin:

https://gitlab.com/wbowling/ssrf1/-/issues/1#note_309127303
{F756269}

### What is the current *bug* behavior?
When importing a model that has a mount_uploader it's possible to use the carrierwave uploader seed attributes to download a file from any host: https://github.com/carrierwaveuploader/carrierwave/wiki/How-to:-Upload-remote-image-urls-to-your-seedfile

### What is the expected *correct* behavior?
The attributes should be prohibited and removed via the `AttributeCleaner`

### Output of checks
This bug happens on gitlab.com

#

## Analysis / Response

**Vulnerability Class:** ssrf
**CWE:** CWE-918
**Weakness:** Server-Side Request Forgery (SSRF)
**Severity:** high
**Endpoint Pattern:** https://github.com/carrierwaveuploader/carrierwave/blob/v1.3.1/lib/carrierwave/mount.rb#L80.

**Impact Assessment:**
* Allows an attacker to access internal services, for example the Omnibus GitLab has all of the exporters, Prometheus, Alertmanager exposed on localhost. 
* If GitLab is hosted on AWS it allows for the instance metadata to be accessed.
* Redis is running locally or accessible via tcp (address could be found by looking at the targets in Prometheus at http://localhost:9090/api/v1/targets) it could be possible to obtain RCE (similar to https://github.com/jas502n/gitlab-SSRF-redis-RCE#poc). A POST request is not possible here, but as `remote_attachment_request_header=` is also available (https://github.com/carrierwaveuploader/carrierwave/blob/v1.3.1/lib/carrierwave/mount.rb#L169) and not blacklisted, the payload could be set via a header.
* If GitLab is hosted on Google Cloud, the above could be used to set the `Metadata-Flavor: Google` header and access `http://metadata.google.internal/`

**Remediation:**
Validate and sanitize all user-supplied URLs. Implement allowlists for permitted domains and IP ranges. Block requests to internal/private IP ranges.

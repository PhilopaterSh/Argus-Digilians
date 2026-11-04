# ACCESS_CONTROL — h1

- source: h1
- class: access_control
- cwe: CWE-284
- severity: medium
- program: shopify
- quality_score: 13

## Scenario

Analyze the following vulnerability report and provide a structured security assessment.

**Report Title:** Collaborators and Staff members without all necessary permissions are able to create, edit and install custom apps
**Affected Asset:** your-store.myshopify.com

**Vulnerability Description:**
## Summary:

### Custom Apps - Permissions

The store owner, collaborators and staff members can create, edit and install custom apps for their shopify store. Therefor, these users need multiple permissions.  The permissions

* `View apps developed by staff and collaborators`
* `Develop apps` and
* `Manage and install apps and channels`

are  all needed. See also https://shopify.dev/apps/auth/admin-app-access-tokens#changing-api-scopes:

> Anyone with a staff or collaborator account on a store can change what store resources an admin-created custom app can access, but only if they have all the following permissions:
    * the Manage and install apps and channels permission and the Develop apps permission
    * the relevant permissions for the respective store resource

### Missing "Manage and install apps and channels" permission

If the `Manage and install apps and channels` permission is finally not granted to a user, custom apps can't be created, edited or installed. The staff user in F1712978 has for example the two permissions `View apps developed by staff and collaborators` and `Develop apps` but **not** the `Manage and install apps and channels` permission. Thus, he is not able to create, edit and install custom apps. He is also not even able to reach the relevant config section at https://<YOUR_STORE>/admin/apps/development  to manage custom apps:  

{F1712979}

Furthermore, the direct usage of the relevant API endpoints is also not possible. The request to create a custom app is not permitted and the server states that the user must have edit permissions for custom apps:

```
POST /admin/internal/web/graphql/core?operation=CreateAppMutation&type=mutation HTTP/2
Host: 19kun-19.myshopify.com
Cookie: [REDACTED_COOKIE]
X-Csrf-Token: <CSRF_STAFF_MEMBER>
Origin: https://19kun-19.myshopify.com
...

{
   "operationName":"CreateAppMutation",
   "variables":{
      "input":{
         "title":"test",
         "maintainerUserId":"gid://shopify/StaffMember/[REDACTED_PHONE]"
      }
   },
   "query":"mutation CreateAppMutation($input: ShopOwnedAppCreateInput!) {\n  shopOwnedAppCreate(input: $input) {\n    app {\n      id\n      title\n      __typename\n    }\n    userErrors {\n      field\n      message\n      code\n      __typename\n    }\n    __typename\n  }\n}\n"
}
```

```
HTTP/2 200 OK
Date: Sat, 30 Apr 2022 20:04:03 GMT
Content-Type: application/json; charset=utf-8
...

{
   "data":{
      "shopOwnedAppCreate":null
   },
   "errors":[
      {
         "message":"Access denied for shopOwnedAppCreate field. Required access: The user must have edit permissions for custom apps.",
         "locations":[
            {
               "line":2,
              

## Analysis / Response

**Vulnerability Class:** access_control
**CWE:** CWE-284
**Weakness:** Improper Access Control - Generic
**Severity:** medium
**Endpoint Pattern:** POST /admin/internal/web/graphql/core?operation=CreateAppMutation&type=mutation

**Impact Assessment:**
A shopify store owner / admin relies on the documentation and assumes that a staff member without the permission to `Manage and install apps and channels` is not able to create, edit or install custom apps. If the store owner / admin now grants a staff member the permission to only one app, the staff member (attacker) is able to

* create and install new custom apps with specific Admin API access scopes
* edit / modify existing custom apps of the store admin / other staff members, including
  * changing Admin API scopes (Integrity)
  * uninstalling the app (Availability)
  * uninstalling / reinstalling the app (which rotates the access keys) (Integrity + Availability)
  * etc.

**Remediation:**
Implement server-side authorization checks on every request. Use role-based access control. Deny by default. Never rely on client-side access control.

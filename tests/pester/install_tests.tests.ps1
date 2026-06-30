# Pester tests for Argus installer
Describe "ARGUS_INSTALLER.ps1" {
    BeforeAll {
        # Dynamically resolve script path relative to this test file
        $installerPath = Join-Path $PSScriptRoot "../../scripts/ARGUS_INSTALLER.ps1"
        if (-not (Test-Path $installerPath)) {
            throw "Installer script not found at expected path: $installerPath"
        }
        . $installerPath
    }

    Context "Config Block Validation" {
        It "Should have correct minimum hardware requirements" {
            $MIN_RAM_GB | Should Be 8
            $MIN_DISK_GB | Should Be 20
        }

        It "Should require Python 3.12" {
            $PYTHON_REQUIRED | Should Be "3.12"
        }

        It "Should have default Kali Linux distro name" {
            $KALI_DISTRO | Should Be "kali-linux"
        }

        It "Should define default virtual environment name" {
            $VENV_NAME | Should Be "Argus_venv"
        }
    }

    Context "Admin Check Helper" {
        It "Test-IsAdministrator should return a boolean value" {
            $result = Test-IsAdministrator
            $result | Should BeOfType [bool]
        }
    }

    Context "Command Execution Helper" {
        It "Test-CommandWorks should return success for standard shell commands" {
            $result = Test-CommandWorks -CommandPath "cmd.exe" -Arguments @("/c", "echo 1")
            $result.Works | Should Be $true
            $result.Output | Should Be "1"
        }

        It "Test-CommandWorks should return failure for invalid commands" {
            $result = Test-CommandWorks -CommandPath "invalidcommand_argus.exe"
            $result.Works | Should Be $false
        }
    }

    Context "Python Discovery Helper" {
        It "Get-UsablePython should return either null or a valid python object matching 3.12" {
            $python = Get-UsablePython
            if ($null -ne $python) {
                $python.Path | Should Not BeNullOrEmpty
                $python.Version | Should Match "3\.12"
            } else {
                # Python 3.12 is not installed on this system, returning null is expected.
                $python | Should BeNull
            }
        }
    }

    Context "Interactive Step Confirmation" {
        It "Confirm-Step should return true without prompting when not interactive" {
            $Interactive = $false
            $result = Confirm-Step -Id 99 -Name "Test Non-Interactive Step"
            $result | Should Be $true
        }
    }
}

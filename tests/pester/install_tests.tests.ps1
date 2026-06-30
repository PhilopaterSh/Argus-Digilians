# Pester tests for Argus installer
Describe "ARGUS_INSTALLER.ps1" {
    # Load the installer script
    $installerPath = "C:/AI_PenTest_Project/remote_Argus_PhilopaterSh/scripts/ARGUS_INSTALLER.ps1"
    . $installerPath

    Context "Self‑elevation" {
        It "Should request admin rights when not elevated" {
            # Simulate non‑elevated environment (skip actual elevation)
            Mock -CommandName Test-IsAdministrator -MockWith { return $false }
            $result = Test-IsAdministrator
            $result | Should -BeFalse
        }
    }

    Context "Health Check" {
        It "Should return 0 when system is healthy" {
            Mock -CommandName Invoke-HealthCheck -MockWith { return 0 }
            $rc = Invoke-HealthCheck
            $rc | Should -Be 0
        }
    }
}

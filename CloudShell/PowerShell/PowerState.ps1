###################################################################################################################################################
#
#  Created By: Craig Newman 
#              Originail version November 28th 2016
#
#
#  Purpose: This script has been developed to support testing of the Fastlab project.  The goal is to provide a script that can be passed a 
#           arguments of VMname and a desired powerstate.
#
#  Usage:   1. Run powershell as an Administrator      
#           2. ./PowerState.ps1  [VMName] [ON/OFF]
#
###################################################################################################################################################
#  Following Removed by Dan - CloudShell will modify these values by string replace
########################################
#param (
#[string] $ThisVM = "",
#[string] $Action = ""
#)

$ThisVM = "~VMName~"
$Action = "~ActionString~"

$VCenterIP = '172.16.4.123'                     #SJ=  '10.10.2.111'    

#### Force the provided parameters to uppercase to avode capitalization issues
$ThisVM = $ThisVM.ToUpper()
$Action = $Action.ToUpper()

#########################################################  Initial Setup #########################################################################

Set-ExecutionPolicy unrestricted | out-null
  if (-not (Get-PSSnapin VMware.VimAutomation.Core -ErrorAction SilentlyContinue)) {
      Add-PSSnapin VMware.VimAutomation.Core | out-null
  }

$VIServer = Connect-VIServer -Server $VCenterIP -User 'PowerShellAutomation' -password 'Adm!n123!' -ea stop | out-null 


if($ThisVM -eq "" -or ($Action -ne "ON" -and $Action -ne "OFF")) {
    Write-host "*Invalid Parameters: Usage is ./PowerState.ps1  [VMName] [ON/OFF]"}
Else{
    ############  Turn it On or Off ####################### 
    If($Action -eq "ON") { get-VM $ThisVM | Start-VM }
    Else{get-VM $ThisVM | stop-vm -Confirm:$false   }
 
}

Disconnect-VIServer -confirm:$false

########################################################################  END  ####################################################################
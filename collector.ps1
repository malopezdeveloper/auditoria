$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
$result = @{identity=@{}; devices=@(); errors=@()}
$queries = @{
 identity='Win32_ComputerSystem'; bios='Win32_BIOS'; cpu='Win32_Processor'; memory='Win32_PhysicalMemory'; disk='Win32_DiskDrive'; battery='Win32_Battery'
}
foreach ($key in $queries.Keys) {
 try {
  $rows = @(Get-CimInstance -ClassName $queries[$key] -OperationTimeoutSec 25 | Select-Object * -ExcludeProperty CimClass,CimInstanceProperties,CimSystemProperties,PSComputerName)
  if ($key -eq 'identity' -or $key -eq 'bios') { $result.identity[$key] = $rows }
  else { foreach ($row in $rows) { $result.devices += @{category=$key; name=$row.Name; id="$key`:$($row.DeviceID):$($row.Tag):$($row.BankLabel)"; details=$row; os_status=$row.Status} } }
 } catch { $result.errors += "$key : $($_.Exception.Message)" }
}
try {
 $pnp = @(Get-PnpDevice -PresentOnly -ErrorAction Stop)
 foreach ($d in $pnp) { $result.devices += @{category=$d.Class; name=$d.FriendlyName; id=$d.InstanceId; os_status=$d.Status; details=@{InstanceId=$d.InstanceId; Class=$d.Class; Problem=$d.Problem; Status=$d.Status}} }
} catch { $result.errors += "PnP: $($_.Exception.Message)" }
$result | ConvertTo-Json -Depth 8 -Compress

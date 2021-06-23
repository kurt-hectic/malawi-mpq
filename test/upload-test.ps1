$filename = "A_ISMC01VBRR071200RRA_C_RJTD_20210607125133_100.bufr"
$date = Get-Date
$date_str = $date.ToString("yyyyMMddHHMMssff")
$new_filename = "TEST_WMO_A_ISMC01VBRR071200RRA_C_RJTD_${date_str}_100.bufr"

aws s3 cp $filename s3://malawi-mqp/incoming/$new_filename

$filename2 = "rep.SNO1.1.16698672652.bufr"
$date2 = Get-Date
$date2_str = $date2.ToString("yyyyMMddHHMMssff")
$new_filename2 = "TEST_WMOrep.SNO1.1.16698672652_${date2_str}.bufr"

aws s3 cp $filename2 s3://malawi-mqp/incoming/$new_filename2

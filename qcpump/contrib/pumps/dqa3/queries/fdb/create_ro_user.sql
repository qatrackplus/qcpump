CONNECT "C:\Path\To\Your\Database\Sncdata.fdb" user "sysdba" password "masterkey";
CREATE USER qcpump PASSWORD 'qcpump';
GRANT SELECT ON atlas_master to USER qcpump;
GRANT SELECT ON dqa3_machine to USER qcpump;
GRANT SELECT ON dqa3_trend to USER qcpump;
GRANT SELECT ON dqa3_data to USER qcpump;
GRANT SELECT ON device to USER qcpump;
GRANT SELECT ON dqa3_calibration to USER qcpump;
GRANT SELECT ON dqa3_template to USER qcpump;
GRANT SELECT ON dqa3_machine to USER qcpump;
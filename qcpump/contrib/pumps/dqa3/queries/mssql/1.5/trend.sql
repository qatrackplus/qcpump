SELECT
    data.Dqa3DataId as data_key,
    data.created as work_started,
    data.AdditionalNotes as comment,
    mach.MachineName as machine_name,
    mach.RoomNumber as room_name,
    mach.MachineId as machine_id,
    data.CollectedBy as signature,
    dev.SerialNumber as device,
    energy.EnergyValue as beamenergy,
    CASE
        WHEN energy.BeamTypeFlag=1 then 'FFF'
        ELSE energy.BeamType
    END as beamtype,
    data.temperature as temperature,
    data.pressure as pressure,

    data.ABDose as dose,
    100*data.ABDose/(100 + data.Dose) as dose_baseline,
    data.Dose as dose_diff,

    data.ABAxialsym as axsym,
    data.ABaxialsym - data.Axialsym as axsym_baseline,
    data.Axialsym as axsym_diff,

    data.ABTrsym as trsym,
    data.ABTrsym - data.Trsym as trsym_baseline,
    data.Trsym as trsym_diff,

    data.ABQaflat as qaflat,
    data.ABQaflat - data.Qaflat as qaflat_baseline,
    data.Qaflat as qaflat_diff,

    CASE
        WHEN energy.BEAMTYPE='Electron' THEN data.ENERGY
        ELSE data.PENERGY
    END as energy,
    0 as energy_baseline,
    CASE
        WHEN energy.BEAMTYPE='Electron' THEN data.ENERGY
        ELSE data.PENERGY
    END as energy_diff,

    data.ABXsize as xsize,
    data.ABXsize - data.Xsize as xsize_baseline,
    data.Xsize as xsize_diff,

    data.ABYsize as ysize,
    data.ABYsize - data.YSize as ysize_baseline,
    data.YSize as ysize_diff,

    data.ABXshift as xshift,
    data.ABXshift - data.XShift as xshift_baseline,
    data.XShift as xshift_diff,

    data.ABYshift as yshift,
    data.ABYshift - data.YShift as yshift_baseline,
    data.YShift as yshift_diff

FROM
    Dqa3Data data
JOIN
    Device dev on data.DeviceId = dev.DeviceId
JOIN
    Dqa3Calibration cal on data.Dqa3CalibrationId = cal.Dqa3CalibrationId
JOIN
    MachineTemplate template on data.MachineTemplateId = template.MachineTemplateId
JOIN
    Machine mach on template.MachineId = mach.MachineId
JOIN
	Energy energy on template.EnergyId = energy.EnergyId
WHERE
    data.created >= ? AND mach.MachineId IN ({units})
ORDER BY data.created asc;

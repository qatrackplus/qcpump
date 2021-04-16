SELECT
    tr.data_key as data_key,
    tr.measured_datetime as work_started
    data.comments as comment,
    mach.mach_key as machine_id,
    mach.tree_name as machine_name,
    room.tree_name as room_name,
    data.signature as signature,
    dev.serial as device,
    template.beamenergy as beam_energy,
    template.beamtype as beam_type,
    template.tree_name as beam_name,
    template.wedgetype as wedge_type,
    template.wedgeangle as wedge_angle,
    template.wedgeorient as wedge_orient,
    data.temperature as temperature,
    data.pressure as pressure,

    tr.ab_dose as dose,
    100*tr.ab_dose/(100 + tr.dose) as dose_baseline,
    tr.dose as dose_diff,

    tr.ab_axialsym as axsym,
    tr.ab_axialsym - tr.axialsym as axsym_baseline,
    tr.axialsym as axsym_diff,

    tr.ab_trsym as trsym,
    tr.ab_trsym - tr.trsym as trsym_baseline,
    tr.trsym as trsym_diff,

    tr.ab_qaflat as qaflat,
    tr.ab_qaflat - tr.qaflat as qaflat_baseline,
    tr.qaflat as qaflat_diff,

    CASE
        WHEN template.BEAMTYPE='Electron' THEN tr.ENERGY
        ELSE tr.PENERGY
    END as energy,
    0 as energy_baseline,
    CASE
        WHEN template.BEAMTYPE='Electron' THEN tr.ENERGY
        ELSE tr.PENERGY
    END as energy_diff,

    tr.ab_xsize as xsize,
    tr.ab_xsize - tr.xsize as xsize_baseline,
    tr.xsize as xsize_diff,

    tr.ab_ysize as ysize,
    tr.ab_ysize - tr.ysize as ysize_baseline,
    tr.ysize as ysize_diff,

    tr.ab_xshift as xshift,
    tr.ab_xshift - tr.xshift as xshift_baseline,
    tr.xshift as xshift_diff,

    tr.ab_yshift as yshift,
    tr.ab_yshift - tr.yshift as yshift_baseline,
    tr.yshift as yshift_diff

FROM
    dqa3_trend tr
JOIN
    dqa3_data data on tr.data_key = data.data_key
JOIN
    device dev on data.device_key = dev.device_key
JOIN
    dqa3_calibration cal on data.cal_key = cal.cal_key
JOIN
    dqa3_template template on data.set_key = template.set_key
JOIN
    dqa3_machine mach on template.mach_key = mach.mach_key
JOIN
    room room on room.ROOM_KEY = mach.ROOM_KEY
WHERE
    tr.measured_datetime >= ? AND mach.mach_key IN ({units})
ORDER BY tr.data_key asc;

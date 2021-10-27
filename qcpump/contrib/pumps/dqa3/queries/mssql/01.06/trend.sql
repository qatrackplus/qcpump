SELECT
    tr.data_key as data_key,
    tr.measured_datetime as work_started,
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

    tr.results_dose as dose,
    tr.rel_baseline_dose as dose_baseline,
    tr.rel_diff_dose as dose_diff,

    tr.results_axsym as axsym,
    tr.rel_baseline_axsym as axsym_baseline,
    tr.rel_diff_axsym as axsym_diff,

    tr.results_trsym as trsym,
    tr.rel_baseline_trsym as trsym_baseline,
    tr.rel_diff_trsym as trsym_diff,

    tr.results_qaflat as qaflat,
    tr.rel_baseline_qaflat as qaflat_baseline,
    tr.rel_diff_qaflat as qaflat_diff,

    CASE
        WHEN template.BEAMTYPE='Electron' THEN tr.REL_DIFF_EENERGY
        ELSE tr.REL_DIFF_XENERGY
    END as energy,
    0 as energy_baseline,
    CASE
        WHEN template.BEAMTYPE='Electron' THEN tr.REL_DIFF_EENERGY
        ELSE tr.REL_DIFF_XENERGY
    END as energy_diff,

    tr.results_xsize as xsize,
    tr.rel_baseline_xsize as xsize_baseline,
    tr.rel_diff_xsize as xsize_diff,

    tr.results_ysize as ysize,
    tr.rel_baseline_ysize as ysize_baseline,
    tr.rel_diff_ysize as ysize_diff,

    tr.results_xshift as xshift,
    tr.rel_baseline_xshift as xshift_baseline,
    tr.rel_diff_xshift as xshift_diff,

    tr.results_yshift as yshift,
    tr.rel_baseline_yshift as yshift_baseline,
    tr.rel_diff_yshift as yshift_diff

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
    tr.measured_datetime >= ?
    AND mach.mach_key IN ({units})
    AND template.beamtype IN ({beam_types})
ORDER BY tr.data_key asc;

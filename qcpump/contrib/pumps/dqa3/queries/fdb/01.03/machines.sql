SELECT
    m.MACH_KEY as machine_id,
    m.TREE_NAME as machine_name,
    R.TREE_NAME as room_name
FROM DQA3_MACHINE m
JOIN ROOM r on r.ROOM_KEY = m.ROOM_KEY
ORDER BY m.MACH_KEY;

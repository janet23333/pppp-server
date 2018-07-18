publish_pattern_task_status_map = dict(
    PENDING=0,
    STARTED=1,
    SUCCESS=2,
    FAILED=3,
    UNREACHABLE=3
)

publish_host_flag_map = {
    'master': 1,
    'slave': 2,
    'gray': 3
}
application_type_map = {
    'web': 1,
    'mod': 2
}

application_type_id_map = {
    1: 'web',
    2: 'mod'
}

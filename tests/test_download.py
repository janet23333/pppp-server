from tasks.publish_plan import down_load_and_archive_package

jenkins_url_list = [
    'http://git.ops.yunnex.com/deployment/packages/raw/ae702abe3b1f8a862cd4f5daab301b985fd4cc45/shop-mod-sms.zip',
]
inventory_version = '07101417'
publish_plan_id = 500
down_load_and_archive_package(jenkins_url_list, inventory_version, publish_plan_id)

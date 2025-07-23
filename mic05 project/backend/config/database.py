# TODO: 替换为需要的mysql数据库信息
TORTOISE_ORM={
    "connections":{
        "default":{
            "engine":"tortoise.backends.mysql",
            "credentials":{
                "host":"",
                "port":3306,
                "user":"",
                "password":"",
                "database":"",
                "charset":"utf8mb4",
                "init_command":"SET time_zone = '+08:00'"
            }
        }
    },
    "apps":{
        "models":{
            "models":["models.history","models.language_stats","aerich.models"],
            "default_connection":"default",
        }
    }
}
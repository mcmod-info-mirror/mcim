
from typing import List
from mysql import *
from config import MysqlConfig
from mysql.command import fields

def create_table(database: DataBase):
    with database:
        cmds = []
        cmds.append(create("curseforge_mod_info",
            fields=fields(("modid","INT", "PRIMARY KEY"), ("status","INT"), ("time", "INT"), ("data", "JSON"))))
        cmds.append(create("curseforge_file_info",
            fields=fields(("modid", "INT"), ("fileid", "INT"), ("status", "INT"), ("time", "INT"), ("data", "JSON"), "PRIMARY KEY (modid, fileid)")))
        cmds.append(create("curseforge_game_info",
            fields=fields(("gameid", "INT", "PRIMARY KEY"), ("status", "INT"), ("time", "INT"), ("data", "JSON"))))
        cmds.append(create("curseforge_mod_description",
            fields=fields(("modid", "INT", "PRIMARY KEY"), ("status", "INT"), ("time", "INT"), ("description", "TEXT"))))
        cmds.append(create("curseforge_file_changelog",
            fields=fields(("modid", "INT"), ("fileid", "INT"), ("status", "INT"), ("time", "INT"), ("changelog", "TEXT"), "PRIMARY KEY (modid, fileid)")))
        cmds.append(create("curseforge_category_info",
            fields=fields(("categoryid","INT", "PRIMARY KEY"), ("status","INT"), ("time", "INT"), ("data", "JSON"))))
        cmds.append(create("modrinth_project_info",
            fields=fields(("project_id","char(8)", "PRIMARY KEY"), ("status","INT"), ("time", "INT"), ("data", "JSON"))))
        cmds.append(create("modrinth_version_info",
            fields=fields(("project_id", "char(8)"), ("version_id", "char(8)"), ("status", "INT"), ("time", "INT"), ("data", "JSON"), "PRIMARY KEY (project_id, version_id)")))
        cmds.append(create("modrinth_tag_info",
            fields=fields(("slug","TEXT", "PRIMARY KEY"), ("status","INT"), ("time", "INT"), ("data", "JSON"))))
        cmds.append(create("mcmod_info",
            fields=fields(("classid", "INT", "PRIMARY KEY"), ("modid", "INT"), ("project_id", "char(8)"), ("status","INT"), ("time", "INT"), ("en_name", "TEXT"), ("zh_name", "TEXT"))))
        for cmd in cmds:
            print(cmd)

if __name__ == "__main__":
    MysqlConfig.load()
    database = DataBase(**MysqlConfig.to_dict())
    create_table(database)

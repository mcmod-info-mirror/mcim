from typing import List
from mysql import *
from config import MysqlConfig

class create_table:
    def __init__(self, database):
        with database:
            cmds = []
            cmds.append(create("curseforge_mod_info", fields=FieldBuilder().f("modid","INT", "PRIMARY KEY").f("status","INT").f("time", "INT").f("data", "JSON")))
            cmds.append(create("curseforge_file_info", fields=FieldBuilder().f("modid", "INT").f("fileid", "INT").f("status", "INT").f("time", "INT").f("data", "JSON").append("PRIMARY KEY (modid, fileid)")))
            cmds.append(create("curseforge_game_info", fields=FieldBuilder().f("gameid", "INT", "PRIMARY KEY").f("status", "INT").f("time", "INT").f("data", "JSON")))
            cmds.append(create("curseforge_mod_description", fields=FieldBuilder().f("modid", "INT", "PRIMARY KEY").f("status", "INT").f("time", "INT").f("description", "TEXT")))
            cmds.append(create("curseforge_file_changelog", fields=FieldBuilder().f("modid", "INT").f("fileid", "INT").f("status", "INT").f("time", "INT").f("changelog", "TEXT").append("PRIMARY KEY (modid, fileid)")))
            cmds.append(create("curseforge_category_info", fields=FieldBuilder().f("categoryid","INT", "PRIMARY KEY").f("status","INT").f("time", "INT").f("data", "JSON")))
            cmds.append(create("modrinth_project_info", fields=FieldBuilder().f("project_id","char(8)", "PRIMARY KEY").f("status","INT").f("time", "INT").f("data", "JSON")))
            cmds.append(create("modrinth_version_info", fields=FieldBuilder().f("project_id", "char(8)").f("version_id", "char(8)").f("status", "INT").f("time", "INT").f("data", "JSON").append("PRIMARY KEY (project_id, version_id)")))
            cmds.append(create("modrinth_tag_info", fields=FieldBuilder().f("slug","char(8)", "PRIMARY KEY").f("status","INT").f("time", "INT").f("data", "JSON")))
            for cmd in cmds:
                database.exe(cmd)

if __name__ == "__main__":
    MysqlConfig.load()
    database = DataBase(**MysqlConfig.to_dict())
    create_table(database)
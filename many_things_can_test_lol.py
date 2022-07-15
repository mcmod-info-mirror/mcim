import yarl
url=yarl.URL(input("输入一个 URI: "))
print("连接协议: " + url.scheme)
print("主机名: " + url.host)
print("端口: " + str(url.port))
print("路径: " + url.path)
print("参数 (String): " + url.query_string)
print("参数: " + str(url.query))
print("页: " + url.fragment)
print("主地址: " + url.parent)
print("测试完成 lol")
pass
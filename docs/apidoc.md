# 发布系统后端API说明



##  package

*  path: /package
*  下载包到目标主机
*  method: `POST`
*  argus:

   ```json
   [
   	{
   	"hosts":["10.10.51.43"],
   	"application_name":"linesvr-mod-service",
   	"version":"1.5.0-032618"
   	}
   ]
   ```

## taskstatu

* path: taskstatu
* 根据taskid 获取任务状态，可多个，逗号隔开
* method: `get`

   示例：

   ```
   http://10.10.50.30:8070/api/taskstatu?taskids=191962da-5182-43e1-b0e4-87ee8aad7c1d
   ```

## deploy

-    path: deploy

-    method: ``

-    argus:


   ```json
   [
     {
     "application_name":"linesvr-mod-service",
     "hosts":["10.10.51.43"],
     "version": "1.5.0-032618"
     }
    ]
   ```

   ​
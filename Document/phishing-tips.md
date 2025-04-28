Bước chuẩn bị
- Nên để C2 để ở local, sau đó dùng 1 con VPS để foward traffic
- Recon được càng nhiều thông tin càng tốt
  + Mạng blacklist những gì? Whitelist những gì?
  + Danh sách email để phishing (có thể cân nhắc dùng gophish)

Bước phishing để vào hệ thống
- Phishing tips:
  + Có thể đặt tên exe là "document.docx                                       .exe" để giả mạo đuôi file .docx
  + Có thể cân nhắc dùng 1 số extension khác có khả năng execute như .lnk, .hta,...
  + Dùng extension spoof
  + Bỏ file exe vào file .zip sau đó đặt tên thật dài để che đi extension .exe
  + Giả mạo mail update phần mềm. Sau đó backdoor vào phần mềm cần cài đặt
  + Nếu chiếm được 1 email, có thể coi nội dung email và hijack vào giữa cuộc trao đổi (Lưu ý: Không khuyến khích vì ảnh hưởng đến luồng mail công việc của khách hàng)
  + Sử dụng kỹ thuật fake captcha phishing
  
Content Phishing
??????

Khi đã vô được hệ thống
- Đẩy scout xuống làm nhiệm vụ do thám
- Dùng/code bof và đẩy cobalt strike xuống cho bước tiếp theo (lateral movement)
- Nên config lại MalleableC2 để tránh bị phát hiện
  + Dùng Burp2Malleable để config lại traffic của cobalt strike cho giống traffic nội bộ
  + Tham khảo 1 số mallable c2 sẵn có trên mạng https://github.com/threatexpress/malleable-c2/tree/master
  
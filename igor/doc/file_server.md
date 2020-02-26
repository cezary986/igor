# File server

Igor works with websockets which works pretty well for text based data but are not meant to handle files especially media files like images. Also native way of working with files (downloading or sending them) on webrowser technologies are based on http or https protocol. For handling files Igor has build in http server which is nothing more than simple native Python http server (from package `http.server`). It is however preconfigured in a way to allow easy file access from your clients processes. 

## Reading files

To read any file from the disk just send `GET` request to the server with the absolute path to it. For example if you want to read a file named `myFile.txt` from `C:\Users\cezary\Desktop\fun` and assuming your Igor file server runs on default port (8080) you need to send following request:

```
GET http://localhost:8080/C:/Users/cezary/Desktop/fun/myFile.txt
```

## Writing files

To write (or overwrite) file you send similar request but now with method `POST` and sending its binary content in raw request body. Example of saving file `myFile.txt`:

```
POST http://localhost:8080/C:/Users/cezary/Desktop/fun/myFile.txt
```

## Renaming, deleting and so on

This operations are not supported nativly by Igor. They are however very easy to implement as simple actions handlers in Igor.


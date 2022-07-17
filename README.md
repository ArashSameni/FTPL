# FTPL - My FTP Like Protocol

> My implementation of FTP both Client and Server in Python3.

## Table of Contents

- [FTPL - My FTP Like Protocol](#ftpl---my-ftp-like-protocol)
  - [Table of Contents](#table-of-contents)
  - [General Info](#general-info)
  - [Features](#features)
  - [Usage](#usage)
  - [Screenshot](#screenshot)

## General Info

The File Transfer Protocol is a standard communication protocol used for transferring files between a server and clients on a computer network. FTP is built on a client–server model architecture using separate control and data connections between the client and the server. This implementation of FTP doesn't fully follow [RFC 959](https://datatracker.ietf.org/doc/html/rfc959) but it implements most of it.

## Features

- Multi-Threaded Server
- Colorful TUI :)
- Readable and clean code
- No external dependencies

## Usage

Put your files inside `server/files` so clients would be able to download it.
Server by default listens on port 2121.

```bash
$ python server/main.py
$ python client/main.py
```

## Screenshot

![FTPL](https://user-images.githubusercontent.com/74505991/179402954-9af2be2f-ec5e-4c32-9d0e-a54c41fbd951.png)

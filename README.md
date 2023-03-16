# jsontrace-upload
JSON Trace Upload lets you upload JSON snapshots to [JSON Trace](https://demo.jsontrace.com/)


### Usage:

You can pipe in JSON data to send to [jsontrace.com](https://demo.jsontrace.com/):
```cat <json> | jtupload.py --name 'label for your use'```

jtupload.py will print out:

```Upload succeeded. You can share this diff with the URL https://demo.jsontrace.com/shared/<hash>```

You can append to the "diff set" by appending a second (or a third, fourth, etc) file to the collection by:

```cat <json> | jtupload.py --name 'another label' --append <hash>```

If you JSON data is in a file, you can tell jtupload.py to upload the file:

```jtupload.py --file <path/to/file>```

If you do not specify a --name, JSON Trace will assign a label for you.

You can upload to the same "diff set" from multiple hosts. For example, you can rapidly compare a JSON file or stream from your laptop to something in EC2 without moving files or copying and pasting. Anyone with the hash can append to the data set, so be careful who you share it with.

Of course, with JSON Trace Pro you can have authenticated sessions so that only you or trusted team members can work with a diff set.

# jsontrace-upload
JSON Trace Upload lets you upload JSON snapshots to [JSON Trace](https://demo.jsontrace.com/) - a powerful visual JSON compare, diff, and analysis tool.


### Usage:

1. Create a bucket in [JSON Trace](https://demo.jsontrace.com/#buckets) by clicking 'create new bucket' if you don't have one. If you already have an empty bucket or if you have too many buckets, you cannot create a new bucket.

![screenshot](https://raw.githubusercontent.com/Data-Culpa/jsontrace-upload/main/readme-images/jt-upload.png)

2. Run `jtupload.py` to push data up to JSON Trace. You can run this script from anywhere--virtual machines in the cloud, a remote data center, a Raspberry Pi, whatever.

```cat <json> | jtupload.py --append <bucket_id> --label 'label for your use'```

Or

```jtupload.py --append <bucket_id> --file <path/to/file/of/json> --label 'label for your use'```

Upon success, `jtupload.py` will print out:

```View your bucket diff at https://demo.jsontrace.com/#view/<hash>```

3. You can append to the "diff set" by appending a second (or a third, fourth, etc) file to the collection by running the above commands again on another JSON source.

If you do not specify a `--label`, JSON Trace will assign a label for you (the current time).

You can upload to the same "diff set" from multiple hosts. For example, you can rapidly compare a JSON file or stream from your laptop to something in EC2 without moving files or copying and pasting. Anyone with the hash can append to the data set, so be careful who you share it with.

Of course, with JSON Trace Pro you can have authenticated sessions so that only you or trusted team members can work with a diff set.

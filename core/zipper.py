import gzip
import io


def compress_string(input_string):
    with io.StringIO() as buffer, gzip.GzipFile(fileobj=buffer, mode='w') as gz_file:
        gz_file.write(input_string)

    compressed_data = buffer.getvalue()

    return compressed_data


def decompress_string(compressed_string):
    with io.StringIO(compressed_string) as buffer, gzip.GzipFile(fileobj=buffer, mode='r') as gz_file:
        decompressed_data = gz_file.read()

    return decompressed_data

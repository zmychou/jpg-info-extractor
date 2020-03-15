import numpy as np


IMAGE = []

markers = {
    'APP1': [0xFF, 0xE1],
    'SOI': [0xFF, 0xD8]
}



class APP1(object):
    attributes_name = {
        271: 'Manufacturer',
        272: 'Model',
        306: 'Last Modify',
        29: 'GPS Date',
        305: 'Software'
    }
    byte_count = {
        'ASCII': 1,
        'BYTE': 1,
        'SHORT': 2,
        'LONG': 4,
        'RATIONAL': 8
    }

    type_of_ifd = {
        1: 'BYTE',
        2: 'ASCII',
        3: 'SHORT',
        4: 'LONG',
        5: 'RATIONAL'
    }

    class Field(object):

        def __init__(self, _tag, _type, _count, _offset, _is_offset):
            self.tag = _tag
            self.type = _type
            self.count = _count
            self.offset = _offset

    exif_identifier = [0x45, 0x78, 0x69, 0x66, 0x00, 0x00]

    def __init__(self, img, app1_offset):
        self._image = img
        self.app1_offset = app1_offset
        self._exif_identifier_offset = 4
        self.tiff_header_length = 8
        self.ifd_offset = 0
        self.little_endian = [0x49, 0x49]
        self.big_endian = [0x4D, 0x4D]
        self.marker = [0xFF, 0xE1]

        self.endian = self._image[self.app1_offset + 10: self.app1_offset + 12]
        self.ifd_offset = self.zero_ifd_offset()
        self.number_of_zero_ifd = self.get_number_of_fields()

    def get_field(self, fields_num, ifd_offset, ):

        fields = []
        for i in range(fields_num):
            start = ifd_offset + 2 + i * 12
            raw_ifd = self._image[start: start + 12]
            tag = self.read_bytes_in_value(raw_ifd[0: 2], False)
            type = self.read_bytes_in_value(raw_ifd[2: 4], False)
            count = self.read_bytes_in_value(raw_ifd[4: 8], False)
            offset = self.read_bytes_in_value(raw_ifd[8: 12], False)

            # todo: evaluate is_offset args
            field = APP1.Field(tag, type, count, offset, False)
            fields.append(field)

        return fields

    def get_fields(self):
        fields = self.get_field(self.number_of_zero_ifd, self.ifd_offset)

       # for i in range(self.number_of_zero_ifd):
       #     start = self.ifd_offset + 2 + i * 12
       #     raw_ifd = self._image[start: start + 12]
       #     tag = self.read_bytes_in_value(raw_ifd[0: 2], False)
       #     type = self.read_bytes_in_value(raw_ifd[2: 4], False)
       #     count = self.read_bytes_in_value(raw_ifd[4: 8], False)
       #     offset = self.read_bytes_in_value(raw_ifd[8: 12], False)

       #     # todo: evaluate is_offset args
       #     field = APP1.Field(tag, type, count, offset, False)
       #     fields.append(field)

        # Get GPS info
        for field in fields:
            if field.tag == 0x8825:
                self.gps_ifd_offset = field.offset + self.tiff_header_offset
                break
        gps_fields_raw = self._image[self.gps_ifd_offset: self.gps_ifd_offset + 2]
        fields_of_gps = self.read_bytes_in_value(gps_fields_raw, False)

        gps_fields = self.get_field(fields_of_gps, self.gps_ifd_offset)

        fields.extend(gps_fields)
        return fields

    def read_attribute(self, field):
        ifd_type = APP1.type_of_ifd[field.type]
        byte_count = APP1.byte_count[ifd_type] * field.count
        start = self.tiff_header_offset + field.offset
        end = start + byte_count
        raw = self._image[start: end]
        if ifd_type == 'ASCII':
            attr = [APP1.attributes_name[field.tag], ': ']
            for r in raw:
                attr.append(chr(r))
            print(''.join(attr))

    def get_number_of_fields(self):
        raw = self._image[self.ifd_offset: self.ifd_offset + 2]
        return self.read_bytes_in_value(raw, False)

    def zero_ifd_offset(self):

        raw = self._image[self.tiff_header_offset + 4: self.tiff_header_offset + 8]
        return self.read_bytes_in_value(raw, False) + self.tiff_header_offset


    def read_bytes_in_value(self, bytes, ignore_endian):
        if not ignore_endian and self.is_little_endian:
            bytes.reverse()
        value = 0
        for byte in bytes:
            value = value << 8
            value = value + byte
        return value


    @property
    def exif_identifier_offset(self):
        return self.app1_offset + self._exif_identifier_offset

    @property
    def tiff_header_offset(self):
        return self.app1_offset + 10

    @property
    def is_little_endian(self):
        endian = self.endian == self.little_endian
        return endian

def compare_bytes(candidate, target):
    return candidate == target

def find_marker(marker, start):
    candidate = copy_bytes(start, 2)
    return marker == candidate

def get_app1_marker_offset():
    length = len(IMAGE)

    for i in range(2, length, 1):
        if find_marker(markers['APP1'], i):
            exif_identifier = copy_bytes(i + 4, 6)
            if compare_bytes(exif_identifier, APP1.exif_identifier):
                return i

    return -1


def copy_bytes(start, length):
    if start > len(IMAGE) or start + length > len(IMAGE):
        raise Exception('Copy bytes fail: out of range.')
    return IMAGE[start: start + length]

def load_image(path):
    n = np.fromfile(path, dtype=np.ubyte)
    n = n.tolist()
    return n

def main():
    global IMAGE
    IMAGE = load_image('1424054533.jpg')
    if not find_marker(markers['SOI'], 0) :
        print('Given image seems not a JPEG image.')
        return

    app1 = APP1(IMAGE, get_app1_marker_offset())
    fields = app1.get_fields()
    for field in fields:
        app1.read_attribute(field)
        if field.tag == 0x8825:
            print('has GPS info')



if __name__ == '__main__':
    main()

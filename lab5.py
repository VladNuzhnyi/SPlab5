# -------------------- Classes --------------------
class addons:
    @staticmethod
    def print_error(*message):
        print('\033[91m', *message, '\033[0m')

    @staticmethod
    def print_ok(*message):
        print('\033[92m', *message, '\033[0m')

    @staticmethod
    def print_descriptor_header():
        print('   №        type  links      length  blocks  name')

    @staticmethod
    def check_state():
        if ActiveFileSystem.FS is None:
            addons.print_error('The file system is not initialised')
            return 1
        return 0

    @staticmethod
    def register_descriptor(descriptor):
        ActiveFileSystem.FS.descriptors.append(descriptor)
        ActiveFileSystem.FS.descriptors_num += 1

    @staticmethod
    def check_path_exist(pathname: str, isLastFile: bool = False):
        if pathname == "":
            return ActiveFileSystem.CWD
        if pathname == '/':
            return ActiveFileSystem.FS.root
        pathArray = pathname.split('/')
        if pathname.startswith('/'):
            localCWD = ActiveFileSystem.FS.root
            pathArray.pop(0)
        else:
            localCWD = ActiveFileSystem.CWD
        new_localCWD = localCWD
        symlink_counter = 0
        if isLastFile:
            j = 0
            while j < len(pathArray):
                if symlink_counter > 20:
                    addons.print_error('Too much symlink')
                    return None
                pathPart = pathArray[j]
                if pathPart == '.':
                    j += 1
                    continue
                if pathPart == '..':
                    new_localCWD = localCWD.parent
                    localCWD = new_localCWD
                    j += 1
                    continue
                arrsize = len(pathArray)
                for i in range(len(localCWD.child_directories)):
                    if pathPart == localCWD.child_directories[i].name:
                        if localCWD.child_directories[i].descriptor.TYPE == 'symlink':
                            symlink_counter += 1
                            symPath = localCWD.child_directories[i].content
                            symPathArr = symPath.split('/')
                            if symPath.startswith('/'):
                                new_localCWD = ActiveFileSystem.FS.root
                                symPathArr.pop(0)
                            for ind, symm in enumerate(symPathArr):
                                pathArray.insert(j + ind + 1, symm)
                            break
                        elif j == len(pathArray) - 1 and localCWD.child_directories[i].descriptor.TYPE == 'regular':
                            return new_localCWD, localCWD.child_directories[i].descriptor
                        elif j == len(pathArray) - 1:
                            return None, None
                        else:
                            new_localCWD = localCWD.child_directories[i]
                            break
                if new_localCWD == localCWD and arrsize == len(pathArray):
                    return None, None
                localCWD = new_localCWD
                j += 1
            return new_localCWD
        else:
            j = 0
            while j < len(pathArray):
                if symlink_counter > 20:
                    addons.print_error('Too much symlink')
                    return None
                pathPart = pathArray[j]
                if pathPart == '.':
                    j += 1
                    continue
                if pathPart == '..':
                    new_localCWD = localCWD.parent
                    localCWD = new_localCWD
                    j += 1
                    continue
                arrsize = len(pathArray)
                for i in range(len(localCWD.child_directories)):
                    if pathPart == localCWD.child_directories[i].name:
                        if localCWD.child_directories[i].descriptor.TYPE == 'symlink':
                            symlink_counter += 1
                            symPath = localCWD.child_directories[i].content
                            symPathArr = symPath.split('/')
                            if symPath.startswith('/'):
                                new_localCWD = ActiveFileSystem.FS.root
                                symPathArr.pop(0)
                            for ind, symm in enumerate(symPathArr):
                                pathArray.insert(j + ind + 1, symm)
                            break
                        else:
                            new_localCWD = localCWD.child_directories[i]
                            break
                if new_localCWD == localCWD and arrsize == len(pathArray):
                    return None
                localCWD = new_localCWD
                j += 1
            return new_localCWD


class ActiveFileSystem:
    BLOCK_SIZE = 64
    MAX_FILE_NAME_LENGTH = 15
    FS = None
    CWD = None


class FileSystem:
    def __init__(self, descriptors_max_num):
        rootDescriptor = Descriptor(0, 'directory', 0, '/')
        rootDescriptor.links_num -= 1
        rootDirectory = Dir('/', rootDescriptor, None)
        ActiveFileSystem.CWD = rootDirectory
        self.descriptors_max_num = descriptors_max_num
        self.descriptors_num = 0
        self.descriptors = []
        self.descriptorsBitmap = [0 for i in range(descriptors_max_num)]
        self.Blocks = {}
        self.opened_files_num_descriptors = []
        self.opened_files = []
        self.descriptors.append(rootDescriptor)
        self.descriptors_num += 1
        self.descriptorsBitmap[0] = 1
        self.root = rootDirectory


class Descriptor:
    def __init__(self, num, file_type, length, name, content=None):
        self.NUM = num
        self.TYPE = file_type
        self.links_num = 1
        self.length = length
        self.blocks = []
        self.name = name
        self.links = [self]
        if file_type == 'symlink':
            self.content = content

    def show_info(self):
        print('%4d  %10s  %5d  %10d  %6d  %s' %
              (self.NUM,
               self.TYPE,
               self.links_num,
               self.length,
               len(self.blocks),
               f'{self.name}->{self.content}' if self.TYPE == 'symlink' else self.name))

    def show_statistics(self):
        print(f'#{self.NUM},{self.TYPE},link_num={self.links_num},length={self.length},blocks_num={len(self.blocks)},'
              f' name={self.name}' + f',symlink to {self.content}' if self.TYPE == 'symlink' else '')


class Link:
    def __init__(self, descriptor, name):
        descriptor.links_num += 1
        self.descriptor = descriptor
        self.name = name

    def show_info(self):
        print('%4d  %10s  %5d  %10d  %6d  %s' %
              (self.descriptor.NUM,
               self.descriptor.TYPE,
               self.descriptor.links_num,
               self.descriptor.length,
               len(self.descriptor.blocks),
               f'{self.name}->{self.descriptor.name}'))

    def show_statistics(self):
        print(f'#{self.descriptor.NUM}, {self.descriptor.TYPE}, links_num={self.descriptor.links_num},'
              f' length={self.descriptor.length}, blocks_num={len(self.descriptor.blocks)},'
              f' name={self.name} links to {self.descriptor.name}')


class fd:
    def __init__(self, descriptor):
        if isinstance(descriptor, Link):
            self.descriptor = descriptor.descriptor
        else:
            self.descriptor = descriptor
        num_desc = 0
        while num_desc in ActiveFileSystem.FS.opened_files_num_descriptors:
            num_desc += 1
        ActiveFileSystem.FS.opened_files_num_descriptors.append(num_desc)
        self.num_descriptor = num_desc
        self.offset = 0


class Symlink:
    def __init__(self, name: str, descriptor: Descriptor, parent, content):
        self.name = name
        self.descriptor = descriptor
        self.parent = parent
        self.content = content


class Dir:
    def __init__(self, name: str, descriptor: Descriptor, parent):
        self.name = name
        if parent is None:
            self.parent = self
        else:
            self.parent = parent
        self.descriptor = descriptor
        self.child_descriptors = []
        self.child_directories = []
        if parent is None:
            parentLink = Link(descriptor, '..')
        else:
            parentLink = Link(parent.descriptor, '..')
        self.child_descriptors.append(parentLink)
        self.child_descriptors.append(Link(descriptor, '.'))


# -------------------- Functions --------------------
def mkfs(n):
    if ActiveFileSystem.FS is not None:
        addons.print_error('The file system was already been initialised')
        return
    ActiveFileSystem.FS = FileSystem(n)
    addons.print_ok('File system is initialised')


def stat(name):
    if addons.check_state():
        return
    oldPath = "/".join(name.split('/')[:-1])
    if len(name.split('/')) == 2 and oldPath == '':
        oldPath = '/'
    descName = name.split('/')[-1]
    workingDir = addons.check_path_exist(oldPath)
    if workingDir is None:
        addons.print_error(f"There is no directory with this path: {oldPath}")
        return
    for descriptor in workingDir.child_descriptors:
        if descriptor.name == descName:
            addons.print_descriptor_header()
            descriptor.show_statistics()
            return
    addons.print_error(f'There is no file with this name: {name}')


def ls(pathname=''):
    if addons.check_state():
        return
    if pathname == '':
        addons.print_descriptor_header()
        for descriptor in ActiveFileSystem.CWD.child_descriptors:
            descriptor.show_info()
        return
    if pathname == '/':
        addons.print_descriptor_header()
        for descriptor in ActiveFileSystem.FS.root:
            descriptor.show_info()
        return
    workingDir = addons.check_path_exist(pathname)
    if workingDir is None:
        addons.print_error(f"There is no directory with this path: {pathname}")
        return
    addons.print_descriptor_header()
    for descriptor in workingDir.child_descriptors:
        descriptor.show_info()


def create(name):
    if addons.check_state():
        return
    oldPath = "/".join(name.split('/')[:-1])
    if len(name.split('/')) == 2 and oldPath == '':
        oldPath = '/'
    descName = name.split('/')[-1]
    if len(str(descName)) > ActiveFileSystem.MAX_FILE_NAME_LENGTH:
        addons.print_error(f'File name is too large. should be less then {ActiveFileSystem.MAX_FILE_NAME_LENGTH}')
    if ActiveFileSystem.FS.descriptors_num >= ActiveFileSystem.FS.descriptors_max_num:
        addons.print_error('All descriptors were used')
        return
    workingDir = addons.check_path_exist(oldPath)
    if workingDir is None:
        addons.print_error(f"There is no directory with this path: {oldPath}")
        return
    for descriptor in workingDir.child_descriptors:
        if descriptor.name == name:
            addons.print_error('File with this name exist')
            return
    descriptor_num = None
    for i, value in enumerate(ActiveFileSystem.FS.descriptorsBitmap):
        if not value:
            ActiveFileSystem.FS.descriptorsBitmap[i] = 1
            descriptor_num = i
            break
    descriptor = Descriptor(descriptor_num, 'regular', 0, descName)
    addons.register_descriptor(descriptor)
    workingDir.child_descriptors.append(descriptor)
    addons.print_descriptor_header()
    descriptor.show_info()


def link(name1, name2):
    if addons.check_state():
        return
    filePath = "/".join(name1.split('/')[:-1])
    if len(name1.split('/')) == 2 and filePath == '':
        filePath = '/'
    descFileName = name1.split('/')[-1]
    workingFileDir = addons.check_path_exist(filePath)
    if workingFileDir is None:
        addons.print_error(f"There is no directory with this path: {filePath}")
        return
    linkPath = "/".join(name2.split('/')[:-1])
    if len(name2.split('/')) == 2 and linkPath == '':
        linkPath = '/'
    descLinkName = name2.split('/')[-1]
    workingLinkDir = addons.check_path_exist(linkPath)
    if workingLinkDir is None:
        addons.print_error(f"There is no directory with this path: {linkPath}")
        return
    if len(str(descLinkName)) > ActiveFileSystem.MAX_FILE_NAME_LENGTH:
        addons.print_error(f'File name is too large. should be less then {ActiveFileSystem.MAX_FILE_NAME_LENGTH}')
    for descriptor in workingLinkDir.child_descriptors:
        if descriptor.name == descLinkName:
            addons.print_error(f'An instance with this name was already created {name2}')
            return
    for descriptor in workingFileDir.child_descriptors:
        if descriptor.name == descFileName:
            if isinstance(descriptor, Descriptor) and descriptor.TYPE == 'symlink':
                addons.print_error('We can\'t do link to symlink file')
                return
            if isinstance(descriptor, Link):
                addons.print_error('You can\'t create link to link')
                return
            new_link = Link(descriptor, descLinkName)
            descriptor.links.append(new_link)
            workingLinkDir.child_descriptors.append(new_link)
            addons.print_descriptor_header()
            new_link.show_info()
            return
    addons.print_error(f'There is no file with name {name1}')


def unlink(name):
    if addons.check_state():
        return
    oldPath = "/".join(name.split('/')[:-1])
    if len(name.split('/')) == 2 and oldPath == '':
        oldPath = '/'
    descName = name.split('/')[-1]
    workingDir = addons.check_path_exist(oldPath)
    if workingDir is None:
        addons.print_error(f'There is no link with given name. It is a file.')
        return
    for descriptor in workingDir.child_descriptors:
        if descriptor.name == descName:
            if isinstance(descriptor, Descriptor):
                if descriptor.TYPE == 'directory':
                    addons.print_error('You can\'t unlink directory')
                    return
                workingDir.child_descriptors.remove(descriptor)
                descriptor.links_num -= 1
                if descriptor.links_num == 0:
                    ActiveFileSystem.FS.descriptorsBitmap[descriptor.NUM] = 0
                    del descriptor
                addons.print_ok('Unlinked')
            else:
                descriptor.descriptor.links_num -= 1
                descriptor.descriptor.links.remove(descriptor)
                workingDir.child_descriptors.remove(descriptor)
                if descriptor.descriptor.links_num == 0:
                    ActiveFileSystem.FS.descriptorsBitmap[descriptor.descriptor.NUM] = 0
                    del descriptor.descriptor
                addons.print_ok('Unlinked')
            return
    addons.print_error(f'There is no link with name {name}')


def symlink(string, pathname):
    if addons.check_state():
        return
    if ActiveFileSystem.FS.descriptors_num >= ActiveFileSystem.FS.descriptors_max_num:
        addons.print_error('All descriptors were used')
        return
    oldPath = "/".join(pathname.split('/')[:-1])
    if len(pathname.split('/')) == 2 and oldPath == '':
        oldPath = '/'
    newSymName = pathname.split('/')[-1]
    if len(str(newSymName)) > ActiveFileSystem.MAX_FILE_NAME_LENGTH:
        addons.print_error(f'File name is too large. should be less then {ActiveFileSystem.MAX_FILE_NAME_LENGTH}')
        return
    if newSymName == '':
        addons.print_error('Name could\'t be empty')
        return
    workingDir = addons.check_path_exist(oldPath)
    if workingDir is None:
        addons.print_error(f"There is no directory with this path: {oldPath}")
        return
    for directory in workingDir.child_directories:
        if newSymName == directory.name:
            addons.print_error('Directory with this name exist')
            return
    descriptor_num = None
    for i, value in enumerate(ActiveFileSystem.FS.descriptorsBitmap):
        if not value:
            ActiveFileSystem.FS.descriptorsBitmap[i] = 1
            descriptor_num = i
            break
    newSymlinkDescriptor = Descriptor(descriptor_num, 'symlink', 0, newSymName, string)
    addons.register_descriptor(newSymlinkDescriptor)
    newSymlink = Symlink(newSymName, newSymlinkDescriptor, workingDir, string)
    workingDir.child_directories.append(newSymlink)
    workingDir.child_descriptors.append(newSymlinkDescriptor)


def open(name):
    if addons.check_state():
        return
    oldPath = "/".join(name.split('/')[:-1])
    if len(name.split('/')) == 2 and oldPath == '':
        oldPath = '/'
    descName = name.split('/')[-1]
    workingDir = addons.check_path_exist(oldPath)
    if workingDir is None:
        addons.print_error(f"There is no directory with this path: {oldPath}")
        return
    for descriptor in workingDir.child_descriptors:
        if descriptor.name == descName:
            if isinstance(descriptor, Descriptor) and descriptor.TYPE == 'symlink':
                addons.print_error('We can\'t open symlink as file')
                return
            openedFile = fd(descriptor)
            ActiveFileSystem.FS.opened_files.append(openedFile)
            addons.print_ok(f'File {name} is opened with id {openedFile.num_descriptor}')
            return
    addons.print_error(f'There is no file with name {name}')


def close(fd):
    if addons.check_state():
        return
    if fd in ActiveFileSystem.FS.opened_files_num_descriptors:
        ActiveFileSystem.FS.opened_files_num_descriptors.remove(fd)
        for openedFile in ActiveFileSystem.FS.opened_files:
            if openedFile.num_descriptor == fd:
                ActiveFileSystem.FS.opened_files.remove(openedFile)
                del openedFile
                addons.print_ok(f'File with id {fd} is closed')
                return
    addons.print_error(f'There is no file opened with ID = {fd}')


def seek(fd, offset):
    if addons.check_state():
        return
    if fd not in ActiveFileSystem.FS.opened_files_num_descriptors:
        addons.print_error(f'There is no opened file with ID = {fd}')
        return
    for openedFile in ActiveFileSystem.FS.opened_files:
        if openedFile.num_descriptor == fd:
            openedFile.offset = offset
            addons.print_ok('Offset was set')
            return


def write(fd, size, val):
    if addons.check_state():
        return
    if len(str(val)) != 1:
        addons.print_error('Val should be 1 byte size')
        return
    if fd not in ActiveFileSystem.FS.opened_files_num_descriptors:
        addons.print_error(f'There is no opened file with ID = {fd}')
        return
    for openedFile in ActiveFileSystem.FS.opened_files:
        if openedFile.num_descriptor == fd:
            num = len(openedFile.descriptor.blocks)
            while openedFile.offset + size > num * ActiveFileSystem.BLOCK_SIZE:
                openedFile.descriptor.blocks.append(['\0' for i in range(ActiveFileSystem.BLOCK_SIZE)])
                num += 1
            num = 0
            for i in range(openedFile.offset + size):
                if i == ActiveFileSystem.BLOCK_SIZE * num + ActiveFileSystem.BLOCK_SIZE:
                    num += 1
                if i >= openedFile.offset:
                    openedFile.descriptor.blocks[num][i - num * ActiveFileSystem.BLOCK_SIZE] = val
            if openedFile.descriptor.length < openedFile.offset + size:
                openedFile.descriptor.length = openedFile.offset + size
            addons.print_ok('Data were written to file')
            return


def read(fd, size):
    if addons.check_state():
        return
    if fd not in ActiveFileSystem.FS.opened_files_num_descriptors:
        addons.print_error(f'There is no opened file with ID = {fd}')
        return
    for openedFile in ActiveFileSystem.FS.opened_files:
        if openedFile.num_descriptor == fd:
            if openedFile.descriptor.length < openedFile.offset + size:
                addons.print_error(
                    f'File length is {openedFile.descriptor.length}. We can\'t read from {openedFile.offset} to {openedFile.offset + size}')
                return
            num = openedFile.offset // ActiveFileSystem.BLOCK_SIZE
            answer = ""
            for i in range(openedFile.offset, openedFile.offset + size):
                if i == ActiveFileSystem.BLOCK_SIZE * num + ActiveFileSystem.BLOCK_SIZE:
                    num += 1
                answer += str(openedFile.descriptor.blocks[num][i - num * ActiveFileSystem.BLOCK_SIZE])
            print(answer)


def truncate(name, size):
    if addons.check_state():
        return
    oldPath = "/".join(name.split('/')[:-1])
    if len(name.split('/')) == 2 and oldPath == '':
        oldPath = '/'
    descName = name.split('/')[-1]
    workingDir = addons.check_path_exist(oldPath)
    if workingDir is None:
        addons.print_error(f"There is no directory with this path: {oldPath}")
        return
    for descriptor in workingDir.child_descriptors:
        if descriptor.name == descName and descriptor.TYPE == 'regular':
            if size < descriptor.length:
                num = len(descriptor.blocks)
                while num * ActiveFileSystem.BLOCK_SIZE > size + ActiveFileSystem.BLOCK_SIZE:
                    descriptor.blocks.pop(num - 1)
                    num -= 1
                descriptor.length = size
            if size > descriptor.length:
                num = len(descriptor.blocks) - 1
                for i in range(descriptor.length, size):
                    if i == ActiveFileSystem.BLOCK_SIZE * num + ActiveFileSystem.BLOCK_SIZE:
                        descriptor.blocks.append(['\0' for i in range(ActiveFileSystem.BLOCK_SIZE)])
                        num += 1
                    descriptor.blocks[num][i - num * ActiveFileSystem.BLOCK_SIZE] = 0
                descriptor.length = size
            addons.print_ok(f'File {name} was successfully truncated')
            return
    addons.print_error(f'There is no file with path {name}')


def mkdir(pathname: str):
    if addons.check_state():
        return
    if ActiveFileSystem.FS.descriptors_num >= ActiveFileSystem.FS.descriptors_max_num:
        addons.print_error('All descriptors were used')
        return
    oldPath = "/".join(pathname.split('/')[:-1])
    if len(pathname.split('/')) == 2 and oldPath == '':
        oldPath = '/'
    newDirName = pathname.split('/')[-1]
    if len(str(newDirName)) > ActiveFileSystem.MAX_FILE_NAME_LENGTH:
        addons.print_error(f'File name is too large. should be less then {ActiveFileSystem.MAX_FILE_NAME_LENGTH}')
    workingDir = addons.check_path_exist(oldPath)
    if workingDir is None:
        addons.print_error(f"There is no directory with this path: {oldPath}")
        return
    for directory in workingDir.child_directories:
        if newDirName == directory.name:
            addons.print_error('Directory with this name exist')
            return
    descriptor_num = None
    for i, value in enumerate(ActiveFileSystem.FS.descriptorsBitmap):
        if not value:
            ActiveFileSystem.FS.descriptorsBitmap[i] = 1
            descriptor_num = i
            break
    newDirDescriptor = Descriptor(descriptor_num, 'directory', 0, newDirName)
    addons.register_descriptor(newDirDescriptor)
    newDir = Dir(newDirName, newDirDescriptor, workingDir)
    workingDir.child_descriptors.append(newDirDescriptor)
    workingDir.child_directories.append(newDir)
    addons.print_ok('Directory is created')


def rmdir(pathname):
    if addons.check_state():
        return
    if pathname == '/':
        addons.print_error('You can\'t delete root directory')
        return
    if pathname == '' or pathname == '.':
        addons.print_error('You can\'t delete current directory')
        return
    if pathname == '..':
        addons.print_error('It\'s unlogical to try delete directory that upper then other. Really? ')
        return
    oldDir = addons.check_path_exist(pathname)
    if oldDir is None:
        addons.print_error(f"There is no directory with this path: {pathname}")
        return
    if len(oldDir.child_descriptors) != 2:
        addons.print_error('You can\'t delete nonempty dir')
        return
    if ActiveFileSystem.CWD == oldDir:
        addons.print_error('You can\'t delete directory you are in now ')
    oldDir.parent.child_descriptors.remove(oldDir.descriptor)
    oldDir.parent.child_directories.remove(oldDir)
    oldDir.child_descriptors.clear()
    oldDir.child_directories.clear()
    oldDir.parent.descriptor.links_num -= 1
    ActiveFileSystem.FS.descriptors.remove(oldDir.descriptor)
    ActiveFileSystem.FS.descriptorsBitmap[oldDir.descriptor.NUM] = 0
    ActiveFileSystem.FS.descriptors_num -= 1
    del oldDir.descriptor
    del oldDir
    addons.print_ok('Directory is deleted')


def cd(pathname):
    if addons.check_state():
        return
    if pathname == '/':
        ActiveFileSystem.CWD = ActiveFileSystem.FS.root
        addons.print_ok('Directory is changed')
        return
    newDir = addons.check_path_exist(pathname)
    if newDir is None:
        addons.print_error(f"There is no directory with this path: {pathname}")
        return
    ActiveFileSystem.CWD = newDir
    addons.print_ok('Directory is changed')


while True:
    try:
        answer_array = input('>>> ').split(' ')
        command = answer_array[0]
        if command == 'mkfs':
            mkfs(int(answer_array[1]))
        elif command == 'stat':
            stat(answer_array[1])
        elif command == 'ls':
            ls()
        elif command == 'create':
            create(answer_array[1])
        elif command == 'link':
            link(answer_array[1], answer_array[2])
        elif command == 'symlink':
            symlink(answer_array[1], answer_array[2])
        elif command == 'unlink':
            unlink(answer_array[1])
        elif command == 'open':
            open(answer_array[1])
        elif command == 'close':
            close(int(answer_array[1]))
        elif command == 'seek':
            seek(int(answer_array[1]), int(answer_array[2]))
        elif command == 'write':
            write(int(answer_array[1]), int(answer_array[2]), answer_array[3])
        elif command == 'read':
            read(int(answer_array[1]), int(answer_array[2]))
        elif command == 'truncate':
            truncate(answer_array[1], int(answer_array[2]))
        elif command == 'mkdir':
            mkdir(answer_array[1])
        elif command == 'rmdir':
            rmdir(answer_array[1])
        elif command == 'cd':
            cd(answer_array[1])
        elif command == 'exit':
            exit(0)
        else:
            addons.print_error('Unknown command')

    except NameError as error:
        addons.print_error('Error in function name')
    except SyntaxError as error:
        addons.print_error('Syntax error')
    except TypeError as error:
        addons.print_error('Arguments error')
    except ValueError as error:
        addons.print_error('Value error')

import pickle, os

# get all dotfiles (which could potentially contain dumped data
dotfiles = [x for x in os.listdir('.') if x.startswith('.')]

objects = []
filenames = []

for filename in dotfiles:
    try:
        # try to de-pickle each dot file
        with open(filename, 'rb') as file:
                objects.append(pickle.load(file))
                filenames.append(filename)
    except:
        pass

#print objects

# prompt for information
oldname = unicode(raw_input("Old username: ").lower())
newname = unicode(raw_input("New username: ").lower())

if oldname == newname:
    print("Names must be different")
    exit()

# replace it in every dotfile, and write it back out
for x in range(0, len(objects)):
    object = objects[x]
    filename = filenames[x]
    
    if newname not in object:
        object[newname] = 0
    
    if oldname in object:
        object[newname] += object[oldname]
        del object[oldname]

        with open(filename, 'wb') as file:
            try:
                pickle.dump(object, file)
                print("Successfully replaced %s with %s in %s" % (oldname, newname, filename))
            except:
                print("File writing error")

    else:
        print("Found no instance of %s in %s" % (oldname, filename))
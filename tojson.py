import pickle, os, json

# get all dotfiles (which could potentially contain dumped data
dotfiles = [x for x in os.listdir('.') if x.startswith('.')]

objects = []
filenames = []

masterjson = {}

for filename in dotfiles:
    try:
        # try to de-pickle each dot file
        with open(filename, 'rb') as file:
            objects.append(pickle.load(file))
            filenames.append(filename)
    except:
        pass

# replace it in every dotfile, and write it back out
for x in range(0, len(objects)):
    object = objects[x]
    filename = filenames[x]

    for key in object:
        if key not in masterjson:
            masterjson[key] = {}
        masterjson[key][filename[1:]] = object[key]

print json.dumps(masterjson, sort_keys=True, indent=4, separators=(',', ': '))

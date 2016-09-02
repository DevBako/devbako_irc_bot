import re
import codecs


Words = {}

def extract_arguments(s):
	flag = True
	l = list(s)
	for i in range(len(l)):
		if l[i] == '"':
			flag = not flag
		if l[i] == '\'' and flag:
			l[i] = '"'
	s = ''.join(l)
	regex = '([^"]\\S*|".+?")\\s*'
	ret = re.findall(re.compile(regex), s)
	return list(map(lambda x: x.strip('"'), ret))


def get_translations(word):
	ret = []
	Depths = {word: 1}
	Stack = [word]
	while len(Stack) > 0:
		cur_word = Stack.pop()
		depth = Depths[cur_word]
		if depth & 1 == 0:
			ret.append(cur_word)
		if cur_word in Words:
			for next_word in Words[cur_word]:
				if next_word not in Depths:
					Stack.append(next_word)
					Depths[next_word] = depth + 1
	return ret

def add_translation(x, y, update_db = True):
	if x not in Words:
		Words[x] = []
	if y not in Words:
		Words[y] = []
	if y not in Words[x]:
		Words[x].append(y)
	if x not in Words[y]:
		Words[y].append(x)
	if update_db:
		with codecs.open('words.txt', 'a', encoding='utf-8') as f:
			f.write(u"%s:%s\n" % (x,y))

def init_translations():
    with codecs.open('words.txt', 'r', encoding='utf-8') as f:
        for line in f:
            x,y = line.strip().split(':')
            add_translation(x, y, False)


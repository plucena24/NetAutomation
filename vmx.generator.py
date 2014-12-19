import os

with open ('C:/DEV5-base Template.vmx') as inf:
 template = inf.read()

for number in [ 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]:
 content = template.format(number=number, datastore = '5357fa02-56aded10-a0dd-90e2ba39d78c')
 directory = 'C:/DEV5 VMX Files/DEV5-R{number:02d}'.format(number=number)
 os.makedirs (directory)
 name = os.path.join (directory, 'DEV5-R{number:02d}.vmx'.format(number=number))

 with open (name, 'w') as outf:
	outf.write(content)

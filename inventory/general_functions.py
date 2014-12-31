# create  a dictionary to store the time value denominations and their respective seconds
# some entries might be 'weeks' and 'week' because of the way data is input, the uptime string may say '2 weeks' or '1 week'
# so instead of storing 'week' and 'weeks', we can just store the character 'w'.

def parse_uptime(uptime_str):

    denoms = {}; 
    denoms['w'] = 604800;
    denoms['d'] = 86400;
    denoms['h'] = 60 * 60;
    denoms['m'] = 60;
    denoms['y'] = 52 * denoms['w'];

    # uptime4 = 'rtr1 uptime is 5 years, 18 weeks, 8 hours, 23 minutes'
    uptime_dict = {}  # dictionary to store the uptime of each router in seconds
    uptime_fields = uptime_str.split(' ')
             
	#However, incrementing by 2 allows us to skip the pairs such as weeks 4,   days 2, etc.
      
    uptime_seconds = sum(int(uptime_fields[i]) * denoms[uptime_fields[i+1][0]] for i in range(0, len(uptime_fields)-1,2))

    return uptime_seconds
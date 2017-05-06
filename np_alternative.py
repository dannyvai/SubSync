import math


def mean_list(numbers):
    sum = 0
    for num in numbers:
        sum += num

    avg = float(sum)/len(numbers)
    return avg

def median_list(list):
    temp = []
    for item in list:
        temp.append(item)

    temp.sort()
    if len(temp)%2 == 0:
        #have to take avg of middle two
        i = len(temp)/2
        median = (temp[i]+temp[i-1])/2.
    else:
        #find the middle (remembering that lists start at 0)
        i = int(len(temp)/2)
        median = temp[i]
    return median

def linspace_list(start,end,num_segments):
    delta = float((end - start))/float(num_segments-1)
    segments = []
    for i in range(0,num_segments):
        segments.append(start+i*delta)

    return segments

def subtract_lists(list1,list2):
    ret = []
    if len(list1) != len(list2):
        print "Error subtracting lists with different sizes"
        return ret
    else:
        for i in range(0,len(list1)):
            ret.append(float(list1[i]) - float(list2[i]))
    return ret

def subtract_list_const(list,c):
    ret = []
    for i in range(0,len(list)):
        ret.append(list[i] - c)
    return ret

def list_where_lt(list,value):
    ret = []

    for i in range(0,len(list)):
        if list[i] < value:
            ret.append(i)

    return ret

def list_where_gt(list,value):
    ret = []

    for i in range(0,len(list)):
        if list[i] > value:
            ret.append(i)
    return ret

def list_abs(list):
    ret = []
    for i in range(0,len(list)):
        ret.append(abs(list[i]))
    return ret

def list_floor(list):
    ret = []
    for i in range(0,len(list)):
        ret.append(math.floor(list[i]))
    return ret

def intersect1d_list(list1,list2):
    ret = []
    for item in list1:
        if item in list2:
            ret.append(item)
    return ret


def interp1d_list(X,Y,x):

    i2 = list_where_gt(X,x)[0]
    i1 = i2 -1
    x1 = X[i1]
    x2 = X[i2]
    y1 = Y[i1]
    y2 = Y[i2]

    y = y1 + (y2-y1)/(x2-x1) * (x-x1);
    return y

def list_on_indices(list,I):
    ret = []
    for i in I:
        ret.append(list[i])
    return ret

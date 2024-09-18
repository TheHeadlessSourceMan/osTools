"""
a console horizontal rule
"""


def hr(msg:str='',ch:str='-',width:int=80):
    """
    a console horizontal rule
    """
    if msg:
        msg=' %s '%msg.strip()
    # figure out the size on each side
    r=width-len(msg)
    l=int(r/2)
    r-=l
    print('%s%s%s'%(ch*l,msg,ch*r))

if __name__=='__main__':
    import sys
    msg=''
    if len(sys.argv)>1:
        msg=' '.join(sys.argv[1:])
    hr(msg)

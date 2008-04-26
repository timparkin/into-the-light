"""Module containing password-related utilities.
"""

import string
import random


def generatePassword(alpha=6,numeric=2):
    """
    Generate a human-readble password consisting of a sequence of letters with
    alternating consonant and vowel, followed by a sequence of digits, followed
    by another alternating sequence of letters. 
    """
    
    vowels = ['a','e','i','o','u']
    consonants = [a for a in string.ascii_lowercase if a not in vowels]
    digits = string.digits
    
    ####utility functions
    def a_part(slen):
        ret = ''
        for i in range(slen):			
            if i%2 ==0:
                randid = random.randint(0,20) #number of consonants
                ret += consonants[randid]
            else:
                randid = random.randint(0,4) #number of vowels
                ret += vowels[randid]
        return ret
    
    def n_part(slen):
        ret = ''
        for i in range(slen):
            randid = random.randint(0,9) #number of digits
            ret += digits[randid]
        return ret
        
    #### 	
    fpl = alpha/2		
    if alpha % 2 :
        fpl = int(alpha/2) + 1 					
    lpl = alpha - fpl	
    
    start = a_part(fpl)
    mid = n_part(numeric)
    end = a_part(lpl)
    
    return "%s%s%s" % (start,mid,end)
    

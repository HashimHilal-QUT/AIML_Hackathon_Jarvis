import nltk
import string
import re 

from nltk.corpus import stopwords
from nltk.stem import PorterStemmer 
from nltk.tokenize import TweetTokenizer


#Example

comment = 'This was really a great experince for me. I will definetly be doing it on the future too. Thank you. Amazing https'

print(f'The Orignial Comment is: {comment}')

def remove_text(comment):

    comment_cleaned = re.sub(r'RT[/s]+',comment)
    comment_cleaned = re.sub(r'#')
    return comment_cleaned


if __name__ == "__main__" :
    comment = remove_text(comment)
    print('Cleaned Comment:',comment)

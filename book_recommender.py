# backend code (Flask example)
from flask import Flask, request, jsonify
import pandas as pd

app = Flask(__name__)

@app.route('/books', methods=['GET'])
def get_books():
    # load data
    ratings = pd.read_csv('BX-Book-Ratings.csv', sep=';', encoding='cp1251', error_bad_lines=False)
    ratings = ratings[ratings['Book-Rating']!=0]
    books = pd.read_csv('BX-Books.csv',  encoding='cp1251', sep=';', error_bad_lines=False)
    ratings=ratings.rename(columns={'User-ID':'user_id', 'Book-Rating': 'ratings'})
    books= books.rename(columns={'Book-Title':'title', 'Book-Author': 'author', 'Year-Of-Publication': 'year', 'Publisher':'publisher'})
    isbnForUser=ratings.groupby('user_id').ISBN.nunique()
    average=sum(isbnForUser.to_dict().values())/len(isbnForUser)
    x=isbnForUser >5
    x=x[x].index.tolist()
    ratings=ratings[ratings['user_id'].isin(x)]
    dataset = pd.merge(ratings, books, on=['ISBN'])
    dataset_lowercase=dataset.apply(lambda x: x.str.lower() if(x.dtype == 'object') else x)
    dataset_lowercase= dataset_lowercase.drop_duplicates(['user_id', 'title'])
    dataset_lowercase=dataset_lowercase.drop(['Image-URL-S', 'Image-URL-M', 'Image-URL-L'], axis=1)
    
    # return books as JSON
    books = dataset_lowercase['title'].tolist()
    return jsonify({'books': books})

if __name__ == '__main__':
    app.run(debug=True)

    

    
    

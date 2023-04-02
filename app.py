import pandas as pd
import numpy as np
from flask import Flask, request, jsonify
from functions import functions

app = Flask(__name__)

@app.route('/recommendations', methods=['POST'])
def get_recommendations():
    data = request.get_json()
    book_title = data['book_title']
    
    ratings = pd.read_csv('BX-Book-Ratings.csv', sep=';', encoding='cp1251', error_bad_lines=False)
    ratings = ratings[ratings['Book-Rating']!=0]

    # load books
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

    dataset_for_corr, ratings_data_raw = functions().Correlation(ratings, books, book_title)
    result, worst = functions().Book_recomendation(book_title, dataset_for_corr, ratings_data_raw)

    recommendations = {}
    recommendations['top_10'] = result.to_dict('records')
    recommendations['bottom_10'] = worst.to_dict('records')

    return jsonify(recommendations)

if __name__ == '__main__':
    app.run()



    

    
    

import pandas as pd
import numpy as np
from flask import Flask, request, jsonify
from functions import functions
import requests

app = Flask(__name__)

class functions:
    def Correlation(self, ratings, books, book_title):

        author_name = dataset_lowercase.loc[dataset_lowercase['title'] == book_title, 'author'].unique()

        author_readers = dataset_lowercase['user_id'][(dataset_lowercase['title']==book_title) & (dataset_lowercase['author'].str.contains(author_name[0]))]
        author_readers = author_readers.tolist()
        books_of_author_readers = dataset_lowercase[(dataset_lowercase['user_id'].isin(author_readers))]

        number_of_rating_per_book = books_of_author_readers.groupby(['title']).agg('count').reset_index()
        books_to_compare = number_of_rating_per_book['title'][number_of_rating_per_book['user_id'] >= 8]
        books_to_compare = books_to_compare.tolist()
        ratings_data_raw = books_of_author_readers[['user_id', 'ratings', 'title', 'author']][books_of_author_readers['title'].isin(books_to_compare)]

        # group by User and Book and compute mean
        #this code is calculating the average rating given by each user for each book they rated
        ratings_data_raw_nodup = ratings_data_raw.groupby(['user_id', 'title'])['ratings'].mean()

        # reset index to see User-ID in every row
        ratings_data_raw_nodup = ratings_data_raw_nodup.to_frame().reset_index()
        ratings_data_raw_nodup

        dataset_for_corr = ratings_data_raw_nodup.pivot(index='user_id', columns='title', values='ratings')
        return dataset_for_corr, ratings_data_raw

    def Book_recomendation(self, book_title, dataset_for_corr, ratings_data_raw):
        dataset_of_other_books = dataset_for_corr.drop(columns=[book_title])
    
        #is calculating the correlation between the book_title column of the dataset_for_corr 
        #and all the other columns in the dataset_of_other_books
        correlations = dataset_of_other_books.corrwith(dataset_for_corr[book_title])
    
        #pandas Series where each index corresponds to a unique book title, 
        #and the value at that index is the average rating for that book
        avgrating = ratings_data_raw.groupby('title')['ratings'].mean()
    
        # Combine correlations and average ratings into a single dataframe
        corr_fellowship = pd.DataFrame({'corr': correlations, 'avg_rating': avgrating})
        corr_fellowship.index.name = 'book'
    
        # Return the best 10 and worst 10 correlated books
        result = corr_fellowship.sort_values('corr', ascending=False).head(10)
        worst = corr_fellowship.sort_values('corr', ascending=True).head(10)
    
        return result, worst


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

    #recommendations = {}
    #recommendations['top_10'] = result.to_dict('records')
    #recommendations['bottom_10'] = worst.to_dict('records')

    #return jsonify(recommendations)
    return result

if __name__ == '__main__':
    app.run()






    

    
    

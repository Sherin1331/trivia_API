import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

def paginate_questions(request, selection):
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [question.format() for question in selection]
    current_questions = questions[start:end]

    return current_questions

# to create an app
def create_app(test_config=None):
    app = Flask(__name__)
    setup_db(app)

    CORS(app, resources={'/': {'origins': '*'}})

# after the request is received
    @app.after_request
    def after_request(response):
        '''
        Sets access control.
        '''
        response.headers.add('Access-Control-Allow-Headers',
                             'Content-Type,Authorization,true')
        response.headers.add('Access-Control-Allow-Methods',
                             'GET,PUT,POST,DELETE,OPTIONS')
        return response

# to get categories
    @app.route('/categories')
    def get_categories():

        categories = Category.query.all()
        categories_dict = {}
        for category in categories:
            categories_dict[category.id] = category.type

        if (len(categories_dict) == 0):
            abort(422)

        return jsonify({
            'success': True,
            'categories': categories_dict
        })

#to get questions
    @app.route('/questions')
    def get_questions():
    
        selection = Question.query.all()
        total_questions = len(selection)
        current_questions = paginate_questions(request, selection)

        categories = Category.query.all()
        categories_dict = {}
        for category in categories:
            categories_dict[category.id] = category.type

        if (len(current_questions) == 0):
            abort(422)

        return jsonify({
            'success': True,
            'questions': current_questions,
            'total_questions': total_questions,
            'categories': categories_dict
        })

#to delete a question
    @app.route('/questions/<int:id>', methods=['DELETE'])
    def delete_question(id):
        '''
        Handles DELETE requests for deleting a question by id.
        '''

        try:
            question = Question.query.filter_by(id=id).one_or_none()

            if question is None:
                abort(422)

            
            question.delete()

            return jsonify({
                'success': True,
                'deleted': id
            })

        except:
            
            abort(400)

#to post a new question
    @app.route('/questions', methods=['POST'])
    def post_question():
        
        body = request.get_json()

        if (body.get('searchTerm')):
            search_term = body.get('searchTerm')

            selection = Question.query.filter(
                Question.question.ilike(f'%{search_term}%')).all()

            if (len(selection) == 0):
                abort(422)

            paginated = paginate_questions(request, selection)

            return jsonify({
                'success': True,
                'questions': paginated,
                'total_questions': len(Question.query.all())
            })
        
        else:
            new_question = body.get('question')
            new_answer = body.get('answer')
            new_difficulty = body.get('difficulty')
            new_category = body.get('category')

           
            if ((new_question is None) or (new_answer is None)
                    or (new_difficulty is None) or (new_category is None)):
                abort(422)

            try:
                question = Question(question=new_question, answer=new_answer,
                                    difficulty=new_difficulty, category=new_category)
                question.insert()

                
                selection = Question.query.order_by(Question.id).all()
                current_questions = paginate_questions(request, selection)

                return jsonify({
                    'success': True,
                    'created': question.id,
                    'question_created': question.question,
                    'questions': current_questions,
                    'total_questions': len(Question.query.all())
                })

            except:
                abort(400)

#to get questions for different categories
    @app.route('/categories/<int:id>/questions')
    def get_questions_by_category(id):

        category = Category.query.filter_by(id=id).one_or_none()

        if (category is None):
            abort(422)

        selection = Question.query.filter_by(category=category.id).all()

        paginated = paginate_questions(request, selection)

        
        return jsonify({
            'success': True,
            'questions': paginated,
            'total_questions': len(Question.query.all()),
            'current_category': category.type
        })

#to create play quiz
    @app.route('/quizzes', methods=['POST'])
    def get_random_quiz_question():
        

        body = request.get_json()

        previous = body.get('previous_questions')

        category = body.get('quiz_category')

        if ((category is None) or (previous is None)):
            abort(422)

        if (category['id'] == 0):
            questions = Question.query.all()
        
        else:
            questions = Question.query.filter_by(category=category['id']).all()

       
        total = len(questions)

       
        def get_random_question():
            return questions[random.randrange(0, len(questions), 1)]

       
        def check_if_used(question):
            used = False
            for q in previous:
                if (q == question.id):
                    used = True

            return used

        
        question = get_random_question()

        
        while (check_if_used(question)):
            question = get_random_question()

          
            if (len(previous) == total):
                return jsonify({
                    'success': True
                })

       
        return jsonify({
            'success': True,
            'question': question.format()
        })

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "success": False,
            "error": 404,
            "message": "resource not found"
        }), 404

    @app.errorhandler(422)
    def unprocessable(error):
        return jsonify({
            "success": False,
            "error": 422,
            "message": "unprocessable"
        }), 422

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            "success": False,
            "error": 400,
            "message": "bad request"
        }), 400

    return app

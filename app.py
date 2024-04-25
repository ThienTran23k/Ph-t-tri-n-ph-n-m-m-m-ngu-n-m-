from flask import Flask, flash, g, jsonify, render_template, request, redirect, url_for
from pymongo import MongoClient
from datetime import datetime
from bson import ObjectId
import secrets
import plotly.express as px
import plotly.io as pio
import io
import base64
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import pandas as pd
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired
from wtforms import StringField, TextAreaField, IntegerField, SubmitField, validators ,SelectField



app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
# Kết nối đến MongoDB
client = MongoClient("mongodb://localhost:27017/")
# Chọn cơ sở dữ liệu, tên cơ sở dữ liệu là "new_restaurant_database"
db = client["new_restaurant_database"]
# Chọn collection, tên collection là "restaurants"
collection = db["restaurants"]


@app.route('/')
def index():
    restaurants = collection.find()  # Lấy dữ liệu từ MongoDB
    return render_template('user.html', restaurants=restaurants)

@app.route('/home')
def home():
    restaurants = collection.find()  # Lấy dữ liệu từ MongoDB
    return render_template('index.html', restaurants=restaurants)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == 'thiensky' and password == '123':
            return render_template('index.html')
    return render_template('login.html')

@app.route('/logout')
def logout():
    # Quay lại trang index.html
    return redirect(url_for('index'))

@app.route('/add_document', methods=['GET', 'POST'])
def add_document():
    if request.method == 'POST':
        # Lấy dữ liệu từ form
        # Lấy dữ liệu từ form
        restaurant_id = request.form['restaurant_id']
        name = request.form['name']
        borough = request.form['borough']
        cuisine = request.form['cuisine']
        building = request.form['building']
        street = request.form['street']
        zipcode = request.form['zipcode']

        grades = []
        grade_dates = request.form.getlist('grade_date')
        grade_grades = request.form.getlist('grade_grade')
        grade_scores = request.form.getlist('grade_score')

        for date, grade, score in zip(grade_dates, grade_grades, grade_scores):
            grade_entry = {
                "date": {"$date": date},
                "grade": grade,
                "score": int(score)
            }
            grades.append(grade_entry)

        # Tạo document từ dữ liệu form
        document = {
            "restaurant_id": restaurant_id,
            "name": name,
            "borough": borough,
            "cuisine": cuisine,
            "address": {
                "building": building,
                "street": street,
                "zipcode": zipcode
            },
            "grades": grades
        }


        # Thêm document vào collection
        insert_result = collection.insert_one(document)
        print(f"Đã thêm tài liệu với ID: {insert_result.inserted_id}")

    return render_template('add_document.html')


@app.route('/update_document', methods=['GET', 'POST'])
def update_document():
    if request.method == 'POST':
        # Lấy restaurant_id từ form
        restaurant_id_to_update = request.form['restaurant_id']
        filter_criteria = {"restaurant_id": restaurant_id_to_update}

        # Truy vấn document cần sửa
        document_to_update = collection.find_one(filter_criteria)

        if not document_to_update:
            print(f"Không tìm thấy tài liệu với Restaurant ID {restaurant_id_to_update}")
            return

        # Lưu restaurant_id vào biến toàn cục g để sử dụng trong template
        g.restaurant_id = restaurant_id_to_update
        # Hiển thị thông tin cũ
        print("Thông tin cũ:")
        print(f"Tên: {document_to_update['name']}")
        print(f"Borough: {document_to_update['borough']}")
        print(f"Cuisine: {document_to_update['cuisine']}")
        print(f"Địa chỉ: {document_to_update['address']['building']} {document_to_update['address']['street']}, {document_to_update['address']['zipcode']}")
        print(f"Grades: {document_to_update['grades']}")

        # Nhập thông tin mới từ form
        new_name = request.form['new_name']
        new_borough = request.form['new_borough']
        new_cuisine = request.form['new_cuisine']

        new_building = request.form['new_building']
        new_street = request.form['new_street']
        new_zipcode = request.form['new_zipcode']

        new_grades = []
        new_grade_dates = request.form.getlist('new_grade_date')
        new_grade_grades = request.form.getlist('new_grade_grade')
        new_grade_scores = request.form.getlist('new_grade_score')

        for date, grade, score in zip(new_grade_dates, new_grade_grades, new_grade_scores):
            grade_entry = {
                "date": {"$date": date},
                "grade": grade,
                "score": int(score)
            }
            new_grades.append(grade_entry)

        # Tạo một dictionary mới chứa thông tin cập nhật
        update_data = {
            "$set": {
                "name": new_name,
                "borough": new_borough,
                "cuisine": new_cuisine,
                "address": {
                    "building": new_building,
                    "street": new_street,
                    "zipcode": new_zipcode
                },
                "grades": new_grades
            }
        }

        # Thực hiện cập nhật
        update_result = collection.update_one(filter_criteria, update_data)


        # Hiển thị kết quả
        print(f"Số tài liệu khớp: {update_result.matched_count}, Số tài liệu sửa đổi: {update_result.modified_count}")
        # Chuyển hướng về trang display_document sau khi cập nhật
        return redirect(url_for('display_document'))

    return render_template('update_document.html')



@app.route('/delete_document', methods=['GET', 'POST'])
def delete_document():
    confirmation_message = None
    restaurant_info = None
    error = None

    if request.method == 'POST':
        # Lấy restaurant_id từ form
        restaurant_id_to_delete = request.form['restaurant_id']

        # Truy vấn cơ sở dữ liệu để lấy thông tin nhà hàng
        restaurant_info = collection.find_one({'restaurant_id': restaurant_id_to_delete})

        if restaurant_info:
            # Thực hiện xóa tài liệu trực tiếp trong MongoDB
            delete_result = collection.delete_one({'restaurant_id': restaurant_id_to_delete})

            # Kiểm tra xem có xóa thành công hay không
            if delete_result.deleted_count > 0:
                # Nếu xóa thành công, hiển thị thông báo xác nhận
                confirmation_message = f"Nhà hàng có ID {restaurant_id_to_delete} đã được xóa thành công."
            else:
                # Nếu không xóa được, đặt biến error
                error = f"Không thể xóa nhà hàng có ID {restaurant_id_to_delete}."
        else:
            # Nếu không tìm thấy nhà hàng, đặt biến error
            error = f"Không tìm thấy nhà hàng có ID {restaurant_id_to_delete}."

    return render_template('delete_document.html', restaurant_info=restaurant_info, confirmation_message=confirmation_message, error=error)



@app.route('/confirm_delete', methods=['POST'])
def confirm_delete():
    if request.method == 'POST':
        # Lấy restaurant_id từ form
        restaurant_id_to_delete = request.form['restaurant_id']

        # Thực hiện xóa tài liệu trực tiếp trong MongoDB
        result = collection.delete_one({'restaurant_id': restaurant_id_to_delete})

        # Kiểm tra xem có xóa thành công hay không
        if result.deleted_count > 0:
            # Nếu xóa thành công, chuyển hướng người dùng đến trang hiển thị thông báo xóa thành công
            flash("Tài liệu với Restaurant ID {} đã được xóa thành công.".format(restaurant_id_to_delete), 'success')
            return redirect(url_for('display_document'))
        else:
            # Nếu không xóa được, gửi thông báo lỗi về template
            flash("Tài liệu với Restaurant ID {} không tồn tại.".format(restaurant_id_to_delete), 'error')

    return render_template('confirm_delete.html')


# Số lượng items trên mỗi trang
ITEMS_PER_PAGE = 10

@app.route('/display_document')
def display_document():
    # Lấy trang hiện tại từ tham số truy vấn
    page = request.args.get('page', 1, type=int)

    # Số lượng tài liệu
    total_documents = collection.count_documents({})

    # Tính chỉ số bắt đầu và kết thúc cho mỗi trang
    start_idx = (page - 1) * ITEMS_PER_PAGE
    end_idx = start_idx + ITEMS_PER_PAGE

    # Truy vấn MongoDB để lấy dữ liệu phân trang và đảo ngược thứ tự theo _id
    documents = collection.find().sort('_id', -1).skip(start_idx).limit(ITEMS_PER_PAGE)

    # Tính tổng số trang
    total_pages = (total_documents + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE

    return render_template('display_document.html', documents=documents, current_page=page, total_pages=total_pages)




@app.route('/quanly')
def quanly():
    return render_template('quanly.html')

@app.route('/thongke')
def thongke():
    return render_template('thongke.html')


@app.route('/display_best_restaurants')
def display_best_restaurants():
    num_top = 20
    best_restaurants_cursor = collection.find().sort([('grades.0.score', -1), ('name', 1)]).limit(num_top)
    best_restaurants = [(restaurant['name'], restaurant['grades'][0]['score']) for restaurant in best_restaurants_cursor]

    app.logger.info("Best Restaurants: %s", best_restaurants)

    return render_template('display_best_restaurants.html', best_restaurants=best_restaurants)

@app.route('/display_worst_restaurants')
def display_worst_restaurants():
    num_low = 10
    worst_restaurants_cursor = collection.find().sort([('grades.0.score', 1), ('name', 1)]).limit(num_low)
    worst_restaurants = [(restaurant['name'], restaurant['grades'][0]['score']) for restaurant in worst_restaurants_cursor]

    app.logger.info("Worst Restaurants: %s", worst_restaurants)

    return render_template('display_worst_restaurants.html', worst_restaurants=worst_restaurants)


@app.route('/display_score_distribution')
def display_score_distribution():
    # Lấy điểm số của tất cả nhà hàng từ MongoDB
    all_scores_cursor = collection.find({}, {'grades.score': 1})

    # Tạo danh sách các điểm số
    scores = []

    for restaurant in all_scores_cursor:
        if 'grades' in restaurant and len(restaurant['grades']) > 0:
            scores.append(restaurant['grades'][0]['score'])

    # Tạo biểu đồ phân bố điểm số
    fig = px.histogram(x=scores, nbins=20, labels={'x': 'Điểm số', 'y': 'Nhà hàng'},
                       title='Phân bố điểm số của các nhà hàng')

    # Lưu biểu đồ dưới dạng HTML
    plotly_html = pio.to_html(fig, full_html=False)

    return render_template('score_distribution.html', plotly_html=plotly_html)



# Định nghĩa route mới để hiển thị đồ thị sử dụng Plotly
@app.route('/count_restaurants_by_borough')
def count_restaurants_by_borough():
    # Lấy dữ liệu về quận của từng nhà hàng
    cursor = collection.find({}, {'borough': 1, 'name': 1})

    # Tạo DataFrame từ dữ liệu
    df = pd.DataFrame(cursor)

    # Đếm số lượng nhà hàng trong từng quận
    borough_counts = df['borough'].value_counts().reset_index()
    borough_counts.columns = ['Quận', 'Số lượng nhà hàng']

    # Tạo đồ thị cột sử dụng Plotly Express
    fig = px.bar(borough_counts, x='Quận', y='Số lượng nhà hàng', title='Đếm số nhà hàng trong từng quận', color='Số lượng nhà hàng', color_continuous_scale='greens')

    # Lưu đồ thị dưới dạng HTML
    plotly_html = pio.to_html(fig, full_html=False)

    return render_template('count_restaurants_by_borough.html', plotly_html=plotly_html)


@app.route('/count_restaurants_by_cuisine')
def count_restaurants_by_cuisine():
    # Lấy dữ liệu về loại ẩm thực của từng nhà hàng
    cursor = collection.find({}, {'cuisine': 1, 'name': 1})

    # Tạo DataFrame từ dữ liệu
    df = pd.DataFrame(cursor)

    # Đếm số lượng nhà hàng theo loại ẩm thực
    cuisine_counts = df['cuisine'].value_counts().reset_index()
    cuisine_counts.columns = ['Loại ẩm thực', 'Số lượng nhà hàng']

    # Tạo đồ thị cột sử dụng Plotly Express
    fig = px.bar(cuisine_counts, x='Loại ẩm thực', y='Số lượng nhà hàng', title='Đếm số lượng nhà hàng theo loại ẩm thực', color='Số lượng nhà hàng', color_continuous_scale='oranges')

    # Lưu đồ thị dưới dạng HTML
    plotly_html = pio.to_html(fig, full_html=False)

    return render_template('count_restaurants_by_cuisine.html', plotly_html=plotly_html)

@app.route('/top_cuisines')
def top_cuisines():
    # Lấy dữ liệu về loại ẩm thực của từng nhà hàng
    cursor = collection.find({}, {'cuisine': 1, 'name': 1})

    # Tạo DataFrame từ dữ liệu
    df = pd.DataFrame(cursor)

    # Đếm số lượng nhà hàng theo loại ẩm thực
    cuisine_counts = df['cuisine'].value_counts()

    # Lấy top N loại ẩm thực phổ biến nhất
    num_top = 10
    top_cuisines = cuisine_counts.head(num_top).reset_index()
    top_cuisines.columns = ['Loại ẩm thực', 'Số lượng nhà hàng']

    # Tạo đồ thị cột sử dụng Plotly Express
    fig = px.bar(top_cuisines, x='Loại ẩm thực', y='Số lượng nhà hàng', title=f'Top {num_top} loại ẩm thực phổ biến nhất', color='Số lượng nhà hàng', color_continuous_scale='purples')

    # Lưu đồ thị dưới dạng HTML
    plotly_html = pio.to_html(fig, full_html=False)

    return render_template('top_cuisines.html', plotly_html=plotly_html)


# Route Flask
@app.route('/count_restaurants_by_grade')
def count_restaurants_by_grade():
    # Lấy dữ liệu về loại đánh giá của từng nhà hàng
    cursor = collection.find({}, {'grades.grade': 1, 'name': 1})

    # Tạo DataFrame từ dữ liệu
    df = pd.DataFrame(cursor)

    # Đếm số lượng nhà hàng theo loại đánh giá
    grade_counts = df['grades'].apply(lambda x: x[0]['grade'] if x else None).value_counts()

    # Kiểm tra xem request có phải là AJAX không
    if 'X-Requested-With' in request.headers and request.headers['X-Requested-With'] == 'XMLHttpRequest':
        # Trả về dữ liệu JSON nếu là AJAX
        return jsonify(grade_counts=grade_counts.to_dict())
    else:
        # Hiển thị đồ thị tròn số lượng nhà hàng theo loại đánh giá nếu là request thông thường
        fig = px.pie(names=grade_counts.index, values=grade_counts.values, title='Đếm số lượng nhà hàng theo loại đánh giá')
        plotly_html = pio.to_html(fig, full_html=False)

        return render_template('count_restaurants_by_grade.html', plotly_html=plotly_html)



# @app.route('/average_score_by_grade')
# def average_score_by_grade():
#     # Lấy dữ liệu về đánh giá của từng nhà hàng
#     cursor = collection.find({}, {'grades': 1, 'name': 1})

#     # Tạo DataFrame từ dữ liệu
#     df = pd.DataFrame(cursor)

#     # Tạo một DataFrame mới với mỗi hàng là một cặp (tên nhà hàng, đánh giá)
#     df_exploded = pd.DataFrame(
#         [(restaurant['name'], grade['grade'], grade['score']) for restaurant in df.to_dict('records') for grade in restaurant.get('grades', [])],
#         columns=['name', 'grade', 'score']
#     )

#     # Tính điểm số trung bình theo loại đánh giá
#     result_df = df_exploded.groupby('grade')['score'].mean().reset_index()

#     # Tạo đồ thị cột điểm số trung bình theo loại đánh giá bằng Plotly Express
#     fig = px.bar(result_df, x='grade', y='score', title='Điểm số trung bình theo loại đánh giá', 
#                  labels={'score': 'Điểm số trung bình'}, color_discrete_sequence=['#e74c3c'])  # Thay đổi màu thành Đỏ Cherry

#     # Lưu đồ thị dưới dạng HTML
#     plotly_html = pio.to_html(fig, full_html=False)

#     # Truyền đồ thị Plotly đã mã hóa vào template HTML để hiển thị
#     return render_template('average_score_by_grade.html', plotly_html=plotly_html)

# Định nghĩa route mới để hiển thị biểu đồ đường
@app.route('/average_score_by_grade')
def average_score_by_grade():
    # Lấy dữ liệu về đánh giá của từng nhà hàng
    cursor = collection.find({}, {'grades': 1, 'name': 1})

    # Tạo DataFrame từ dữ liệu
    df = pd.DataFrame(cursor)

    # Tạo một DataFrame mới với mỗi hàng là một cặp (tên nhà hàng, đánh giá)
    df_exploded = pd.DataFrame(
        [(restaurant['name'], grade['grade'], grade['score']) for restaurant in df.to_dict('records') for grade in restaurant.get('grades', [])],
        columns=['name', 'grade', 'score']
    )

    # Tính điểm số trung bình theo loại đánh giá
    result_df = df_exploded.groupby('grade')['score'].mean().reset_index()

    # Tạo biểu đồ đường bằng Plotly Express
    fig = px.line(result_df, x='grade', y='score', title='Điểm số trung bình theo loại đánh giá',
                  labels={'score': 'Điểm số trung bình'}, line_shape='linear')

    # Lưu biểu đồ dưới dạng HTML
    plotly_html = pio.to_html(fig, full_html=False)

    # Truyền đồ thị Plotly đã mã hóa vào template HTML để hiển thị
    return render_template('average_score_by_grade.html', plotly_html=plotly_html)





# Route chính để hiển thị trang người dùng
@app.route('/user')
def user():
    return render_template('user.html')

@app.route('/display_document_user')
def display_document_user():

    # Lấy trang hiện tại từ tham số truy vấn
    page = request.args.get('page', 1, type=int)

    # Số lượng tài liệu
    total_documents = collection.count_documents({})

    # Tính chỉ số bắt đầu và kết thúc cho mỗi trang
    start_idx = (page - 1) * ITEMS_PER_PAGE
    end_idx = start_idx + ITEMS_PER_PAGE

    # Truy vấn MongoDB để lấy dữ liệu phân trang và đảo ngược thứ tự theo _id
    documents = collection.find().sort('_id', -1).skip(start_idx).limit(ITEMS_PER_PAGE)

    # Tính tổng số trang
    total_pages = (total_documents + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE

    return render_template('display_document_user.html', documents=documents, current_page=page, total_pages=total_pages, form=ReviewForm())



class ReviewForm(FlaskForm):
    restaurant_id = StringField('ID Nhà Hàng', validators=[validators.DataRequired()])
    user = StringField('Tên Người Dùng', validators=[validators.DataRequired()])
    comment = TextAreaField('Bình Luận', validators=[validators.DataRequired()])
    rating = IntegerField('Đánh Giá (từ 1 đến 5)', validators=[validators.NumberRange(min=1, max=5)])
    submit = SubmitField('Gửi Đánh Giá')

@app.route('/user_grade', methods=['GET', 'POST'])
def user_grade():
    form = ReviewForm()

    if request.method == 'POST' and form.validate_on_submit():
        restaurant_id = form.restaurant_id.data  # Lấy ID của nhà hàng từ form
        user = form.user.data
        comment = form.comment.data
        rating = form.rating.data
        review_entry = {
            "user": user,
            "comment": comment,
            "rating": rating,
            "date": datetime.now()
        }

        # Thêm đánh giá và bình luận vào tài liệu
        collection.update_one(
            {"restaurant_id": restaurant_id},
            {"$push": {"reviews": review_entry}}
        )

        # Hiển thị thông báo thành công hoặc chuyển hướng người dùng đến trang khác
        # Ở đây, tôi chuyển hướng về trang display_document_user
        return redirect(url_for('display_document_user'))

    # Truyền giá trị restaurant_id từ request vào biến toàn cục g
    g.restaurant_id = request.args.get('restaurant_id', None)

    # Nếu restaurant_id có giá trị, set giá trị này cho trường restaurant_id trong form
    if g.restaurant_id:
        form.restaurant_id.data = g.restaurant_id

    return render_template('user_grade.html', form=form)



if __name__ == '__main__':
    app.run(debug=True)
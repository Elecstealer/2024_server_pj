from flask import Flask, render_template, session, url_for, request, redirect
import pymysql

app = Flask(__name__)
app.secret_key = 'sample_secret'

def connectsql():
    conn = pymysql.connect(host='localhost', user='root', passwd='1234', db='server_db', charset='utf8')
    return conn

@app.route('/home', methods=['GET'])
def home():
    # 로그인한 사용자의 세션 확인
    if 'username' not in session:
        return redirect('/')
    
    query = request.args.get('query', '')
    conn = connectsql()
    cursor = conn.cursor()
    
    if query:  # 검색어가 있을 경우
        cursor.execute("SELECT * FROM contest_list WHERE contest_name LIKE %s", ('%' + query + '%',))
    else:  # 검색어가 없을 경우 모든 공모전 조회
        cursor.execute("SELECT * FROM contest_list")
        
    contest_list = cursor.fetchall()
    cursor.close()
    conn.close()
    image_list = [contest[5] for contest in contest_list]
    print(image_list)

    return render_template('home.html', contest_list=contest_list, image_list=image_list, query=query)

@app.route('/page/<id>', methods=['GET', 'POST'])
def page(id):
    if 'username' in session:
        username = session['username']

        conn = connectsql()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        query = "SELECT id, contest_name, contest_dec, contest_join, contest_winner FROM contest_list WHERE id = %s"
        value = id
        cursor.execute(query, value)
        content = cursor.fetchall()
        conn.commit()
        cursor.close()
        conn.close()
        
        return render_template('page.html', data=content, username=username)
    else:
        return redirect('/login')

@app.route('/page/memberpost/<id>', methods=['GET', 'POST'])
def memberpost(id):
    if 'username' in session:
        username = session['username']
        
        conn = connectsql()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        query = "SELECT id, title, content, time, username, value FROM join_list WHERE value = %s"
        cursor.execute(query, id)
        join_data = cursor.fetchall()
        cursor.close()
        conn.close()
    
    return render_template("memberpost.html", postlist=join_data, logininfo=username)

@app.route('/page/memberpost/memberview/<id>', methods=['GET', 'POST'])
def memberview(id):
    conn = connectsql()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    query = "SELECT id, title, content, value FROM join_list WHERE id = %s"
    cursor.execute(query, (id,))
    post = cursor.fetchone()

    if request.method == 'POST':
        if 'username' in session:
            username = session['username']
            comment = request.form['comment']

            query = "INSERT INTO comments (post_id, username, comment) VALUES (%s, %s, %s)"
            cursor.execute(query, (id, username, comment))
            conn.commit()

    query = "SELECT id, username, comment, created_at FROM comments WHERE post_id = %s"
    cursor.execute(query, (id,))
    comments = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('memberview.html', post=post, comments=comments, logininfo=session.get('username'))

@app.route('/page/memberpost/memberview/delete/<comment_id>', methods=['POST'])
def delete_comment(comment_id):
    if 'username' in session:
        username = session['username']
        
        conn = connectsql()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        query = "SELECT post_id FROM comments WHERE id = %s"
        cursor.execute(query, (comment_id,))
        post_id = cursor.fetchone()['post_id']
        
        query = "SELECT * FROM comments WHERE id = %s AND username = %s"
        cursor.execute(query, (comment_id, username))
        comment = cursor.fetchone()
        
        if comment:
            delete_query = "DELETE FROM comments WHERE id = %s"
            cursor.execute(delete_query, (comment_id,))
            conn.commit()
            
        cursor.close()
        conn.close()
    
        return redirect(url_for('memberview', id=post_id))
    else:
        return render_template("login.html")


@app.route('/page/memberpost/memberview/delete/<id>')
def delete(id):
    if 'username' in session:
        username = session['username']
        conn = connectsql()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        query = "SELECT username, value FROM join_list where id = %s"
        values = id
        cursor.execute(query, values)
        post_list = cursor.fetchall()

        page_value = [post_list[0]['value']]
        name = [post_list[0]['username']]

        if username in name:
            query = "DELETE FROM join_list WHERE id = %s"
            value = id
            cursor.execute(query, value)
            conn.commit()
            cursor.close()
            conn.close()

            print(page_value[0])
            return redirect(url_for('memberpost', id=page_value[0]))
        else:
            return "게시글을 삭제할 수 없습니다."
        
@app.route('/page/memberpost/memberview/edit/<id>', methods=['GET', 'POST'])
def edit(id):
    if request.method == 'POST':
        if 'username' in session:
            username = session['username']

            edittitle = request.form['title']
            editcontent = request.form['content']

            conn = connectsql()
            cursor = conn.cursor()
            query = "UPDATE join_list SET title = %s, content = %s WHERE id = %s"
            value = (edittitle, editcontent, id)
            cursor.execute(query, value)
            conn.commit()
            cursor.close()
            conn.close()

            return redirect(url_for('memberview', id=id))

    else:
        if 'username' in session:
            username = session['username']
            conn = connectsql()
            cursor = conn.cursor()
            query = "SELECT username FROM join_list WHERE id = %s"
            value = id
            cursor.execute(query, value)
            data = [post[0] for post in cursor.fetchall()]
            cursor.close()
            conn.close()

            if username in data:
                conn = connectsql()
                cursor = conn.cursor(pymysql.cursors.DictCursor)
                query = "SELECT id, title, content FROM join_list WHERE id = %s"
                value = id
                cursor.execute(query, value)
                postdata = cursor.fetchall()
                cursor.close()
                conn.close()
                return render_template('postupdate.html', data=postdata, logininfo=username)
            else:
                return "게시글을 수정할 수 없습니다."
        else:
            return redirect(url_for('memberview', id=id))
       
@app.route('/page/memberpost/postwrite/<int:id>', methods=['GET', 'POST'])
def postwrite(id):
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        conn = connectsql()
        cursor = conn.cursor() 
        query = "INSERT INTO join_list (title, content, time, username, value) VALUES (%s, %s, NOW(), %s, %s)"
        values = (title, content, username, id)
        cursor.execute(query, values)
        conn.commit()
        cursor.close()
        conn.close()

        return redirect(url_for('memberpost', id=id))
    
    return render_template("postwrite.html", id=id, logininfo=username)

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.pop('username', None)
    return render_template('login.html')
    

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        new_username = request.form['username']
        new_password = request.form['password']

        conn = connectsql()
        cursor = conn.cursor()
        query = "SELECT * FROM users WHERE username=%s AND password=%s"
        value = (new_username, new_password)
        cursor.execute(query, value)
        data = cursor.fetchall()
        cursor.close()
        conn.close()

        for row in data:
            data = row[0]

        if data:
            session['username'] = new_username
            return redirect('/home')
        else:
            error_message = "Invalid username or password"
            return render_template('login.html', error_message=error_message)
        
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']

        conn = connectsql()
        cursor = conn.cursor()
        query = "SELECT * FROM users WHERE username = %s"
        value = username
        cursor.execute(query, value)
        data = cursor.fetchall()

        if data:
            return render_template('registError.html')
        
        else:
            query = "INSERT INTO users (username, password, email) VALUES (%s, %s, %s)"
            value = (username, password, email)
            cursor.execute(query, value)
            data = (cursor.fetchall())
            conn.commit()
            cursor.close()
            conn.close()

            return render_template('mypage.html')
        
    return render_template('signup.html')

from flask import render_template

@app.route('/mypage_view')
def mypage_view():
    if 'username' in session:
        if 'username' in request.args:
            username = request.args['username']
        else:
            username = session['username']
        
        conn = connectsql()

        cursor = conn.cursor(pymysql.cursors.DictCursor)
        query = "SELECT username, major, grade, completed_projects, ongoing_projects, introduction, phone, email FROM my_page WHERE username = %s"
        cursor.execute(query, (username,))
        mypage = cursor.fetchone()

        cursor.close()
        conn.close()

        if mypage is None:
            return render_template('mypage.html', logininfo=username)
        else:
            # 변수명을 템플릿과 일치시키기
            mypage['projects'] = 0  # projects와 in_progress는 예시로 추가했습니다.
            mypage['in_progress'] = 0  # 실제 값으로 교체해야 합니다.
            return render_template('mypage_view.html', mypage=mypage, logininfo=username)
    else:
        return redirect('/login')

@app.route('/mypage', methods=['GET', 'POST'])
def mypage():
    if 'username' in session:
        if request.method == 'POST':
            # 양식 제출 처리
            username = session['username']
            major = request.form['major']
            grade = request.form['grade']
            completed_projects = request.form['completed_projects']
            ongoing_projects = request.form['ongoing_projects']
            introduction = request.form['introduction']
            phone = request.form['phone']
            email = request.form['email']
            
            # 데이터베이스에 사용자의 프로필 정보 저장 또는 업데이트
            conn = connectsql()
            cursor = conn.cursor()
            try:
                # 사용자의 프로필 정보가 이미 있는지 확인합니다.
                cursor.execute("SELECT * FROM my_page WHERE username = %s", (username,))
                existing_profile = cursor.fetchone()

                if existing_profile:  # 프로필 정보가 이미 존재하는 경우
                    # 프로필 정보를 업데이트합니다.
                    query = """UPDATE my_page
                               SET 
                                   major = %s,
                                   grade = %s,
                                   completed_projects = %s,
                                   ongoing_projects = %s,
                                   introduction = %s,
                                   phone = %s,
                                   email = %s
                               WHERE
                                   username = %s"""
                    values = (major, grade, completed_projects, ongoing_projects, introduction, phone, email, username)
                else:  # 최초 등록인 경우
                    # 프로필 정보를 새로 추가합니다.
                    query = """INSERT INTO my_page (username, major, grade, completed_projects, ongoing_projects, introduction, phone, email)
                               VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
                    values = (username, major, grade, completed_projects, ongoing_projects, introduction, phone, email)

                cursor.execute(query, values)
                conn.commit()
            except Exception as e:
                print(f"데이터 저장 중 오류 발생: {e}")
                return "데이터 저장 중 오류가 발생했습니다."
            finally:
                cursor.close()
                conn.close()
            
            return redirect('/home')

        else:
            # 최초 등록 양식을 보여줍니다.
            return render_template('mypage.html')
    else:
        # 사용자가 로그인되지 않은 경우 로그인 페이지로 리디렉션
        return redirect('/login')


@app.route('/main', methods=['GET', 'POST'])
def main():
    if 'username' in session:
        username = session['username']

        return render_template('main.html')
    else:
        username = None
        return redirect('/')
    
if __name__ == '__main__':
    app.run(debug=True)

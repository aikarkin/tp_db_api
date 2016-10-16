#!flask/bin/python
from flask import Flask, jsonify, request
from mysql.connector import errorcode
import mysql.connector

app = Flask(__name__)
tables = ['follower', 'forum', 'post', 'subscribe', 'thread', 'user']
db = mysql.connector.connect(host="localhost",
                             user="root",
                             passwd="euqvuips",
                             database="forum")


class BadRequest(Exception):
    status_code = 2

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_json(self):
        return jsonify({"code": self.status_code, "response": self.message})


def on_json_parse_error(self):
    raise BadRequest('invalid json', status_code=2)


def execute(statement, dic=False, statement_type=None):
    try:
        cur = db.cursor(dictionary=dic)
        cur.execute(statement)
        return cur
    except mysql.connector.DataError:
        raise BadRequest("Invalid request: semantically incorrect query", status_code=3)
    except mysql.connector.IntegrityError:
        if statement_type is None:
            statement_type = statement.split(" ")[0]
        if statement_type is "INSERT":
            raise BadRequest("Invalid request: Entity with current key already exist", status_code=0)
        else:
            raise BadRequest("Invalid request: the relational integrity of the data is affected", status_code=3)
    except mysql.connector.InternalError:
        raise BadRequest("MySQL server encounters an internal error", status_code=4)
    except mysql.connector.OperationalError:
        raise BadRequest("MySQL operation error", status_code=4)
    except mysql.connector.ProgrammingError as err:
        if err.errno == errorcode.ER_SYNTAX_ERROR:
            raise BadRequest("Invalid query: check your syntax!", status_code=4)
        else:
            raise BadRequest("Invalid query: {}".format(err), status_code=4)


@app.route('/')
def index():
    specification_url = 'https://github.com/s-stupnikov/technopark-db-api/blob/master/README.md'
    tp_url = 'http://park.mail.ru/'
    resp = "<h3>Forum RESTful API</h3> " \
           "<p>Created for study Data Base courses in <a href=\'{0}\'>park.mail.ru</a>.</p> " \
           "See <a href=\'{1}\'>specification</a> for details.".format(tp_url, specification_url)
    return resp


@app.route('/db/api/clear', methods=['GET'])
def clear():
    try:
        for table_name in tables:
            execute("TRUNCATE %s" % table_name)
        resp = {'code': 0, 'response': 'OK'}
        return jsonify(resp)
    except BadRequest as err:
        return err.to_json()


@app.route('/db/api/status', methods=['GET'])
def status():
    try:
        table_to_count = {}
        for table_name in tables:
            cur = execute("SELECT COUNT(*) FROM %s" % table_name)
            table_to_count[table_name] = cur.fetchone()[0]
        resp = {'code': 0, 'response': table_to_count}
        return jsonify(resp)
    except BadRequest as err:
        return err.to_json()


@app.route('/db/api/forum/create', methods=['POST'])
def forum_create():
    try:
        request.on_json_loading_failed = on_json_parse_error
        req_data = request.get_json()
        name = req_data["name"]
        short_name = req_data["short_name"]
        user = req_data["user"]
        statement = "INSERT INTO forum (name, slug, user) VALUES (\'%s\', \'%s\', \'%s\');" % (name, short_name, user)
        cur = execute(statement)
        return jsonify({'code': 0,
                        'response': {'id': cur.lastrowid, 'name': name, 'short_name': short_name, 'user': user}
                        })
    except BadRequest as err:
        return err.to_json()
    except TypeError:
        return jsonify({'code': 2, 'response': 'invalid json: unknown key'})


@app.route('/db/api/forum/details', methods=['GET'])
def forum_details():
    request.on_json_loading_failed = on_json_parse_error
    data = request.get_json()
    # request has related user
    if data['related'] is not None:
        if data['related'][0] is "user":
            try:
                # getting forum and user info
                forum_user_state = "SELECT " \
                                "forum.id, " \
                                "forum.name, " \
                                "forum.slug, " \
                                "user.about, " \
                                "user.email, " \
                                "user.id AS 'user_id', " \
                                "user.isAnonymous, " \
                                "user.name AS 'user_name', " \
                                "user.username AS 'username' " \
                            "FROM forum, user " \
                            "WHERE forum.user=user.email AND forum.slug=\'{}\';".format(data['forum'])
                cur = execute(statement=forum_user_state)
                forum_row = cur.fetchone()

                # getting followers
                user_followers_state = "SELECT * FROM follower WHERE follower_mail=\'{}\';".format(forum_row['email'])
                cur = execute(statement=user_followers_state)
                user_followers_rows = cur.fetchall()

                # getting followings
                user_following_state = "SELECT * FROM follower WHERE following_mail=\'{}\';".format(forum_row['email'])
                cur = execute(statement=user_following_state)
                user_following_rows = cur.fetchall()

                # getting subscribes
                user_subscribe_state = "SELECT * FROM subscribe WHERE user=\'{}\';".format(forum_row['email'])
                cur = execute(statement=user_subscribe_state)
                user_subscribe_rows = cur.fetchall()
            except BadRequest as err:
                return err.to_json()
        else:
            return jsonify({'code': 3, 'response': 'unknown key in json'})
    # no related user in request
    else:
        forum_state = "SELECT * FROM forum WHERE slug=\'{}\';".format(data['forum'])
        cur = execute(statement=forum_state)
        forum_row = cur.fetchone()

    # forming response object
    if data['related'] is not None:
        user = {'about': forum_row['about'], 'email': forum_row['email'], 'followers': [], 'following': []}
        for follower_row in user_followers_rows:
            user['followers'].append(follower_row[0])
        for following_row in user_following_rows:
            user['following'].append(following_row[1])
        user['id'] = forum_row['user_id']
        user['isAnonymous'] = forum_row['isAnonymous']
        user['name'] = forum_row['user_name']
        for subscribe_row in user_followers_rows:
            user['subscriptions'].append(subscribe_row[2])
        user['username'] = forum_row['username']
    else:
        user = forum_row['user']
    resp = {'id': forum_row['id'], 'name': forum_row['name'], 'short_name': forum_row['slug'], 'user': user}
    return jsonify(resp)


if __name__ == '__main__':
    app.run(debug=True)

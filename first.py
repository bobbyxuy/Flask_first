from flask import Flask, render_template, session, url_for, redirect, flash
from flask_bootstrap import Bootstrap  # 界面模板
from flask_moment import Moment  # 日期格式调整
from datetime import datetime   # 调用时间utc时间
from flask_wtf import Form  # Web表单
from wtforms import StringField, SubmitField  # 表单样式
from wtforms.validators import DataRequired
from flask_sqlalchemy import SQLAlchemy
import os
from flask_script import Shell, Manager  # 集成python shell
from flask_mail import Mail, Message  # 邮件
from threading import Thread


basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)  # app为Flask的实例
bootstrap = Bootstrap(app)  # bootstrap为Bootstrap的实例
moment = Moment(app)

app.config['SECRET_KEY'] = 'hard to guess string'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'data.sqlite')
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True  # 新增
db = SQLAlchemy(app)
manager = Manager(app)
app.config['MAIL_SERVER'] = 'smtp.qq.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['FLASKY_MAIL_SUBJECT_PREFIX'] = '[FLasky]'
app.config['FLASKY_MAIL_SENDER'] = 'BOBBY<XYZ1219@QQ.COM>'
app.config['FLASKY_ADMIN'] = os.environ.get('FLASKY_ADMIN')
mail = Mail(app)  # 顺序问题，需要先配置smtp配置，再初始化


class NameForm(Form):
    name = StringField('What is your name?', validators=[DataRequired()])
    submit = SubmitField('Submit')


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)  # 普通整数，int，主键
    name = db.Column(db.String(64), unique=True)  # unique不允许有相同的值出现
    users = db.relationship('User', backref='role', lazy='dynamic')  # User:表明与哪个类型相关联，backrefer 向User模型中添加role属性，从而定义反向关系

    def __repr__(self):
        return '<Role %r>' % self.name


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)  # index：为这列创建索引，提升查询效率
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))  # 外键，链接？ roles.id：这列值是roles表中的id

    def __repr__(self):  # 定义__repr()__方法，返回一个具有可读性的字符串表示模型，可在调试和测试时使用
        return '<User %r>' % self.username


def send_async_email(app,msg):
    with app.app_context():
        mail.send(msg)


def make_shell_context():
    return dict(app=app, db=db, User=User, Role=Role)
manager.add_command("shell", Shell(make_context=make_shell_context))


def send_email(to, subject, template, **kwargs):
    msg = Message(
        app.config['FLASKY_MAIL_SUBJECT_PREFIX'] + subject, sender=app.config['FLASKY_MAIL_SENDER'],
        recipients=[to])
    msg.body = render_template(template + '.txt', **kwargs)
    msg.html = render_template(template + '.html', **kwargs)
    thr = Thread(target=send_async_email,args=[app, msg])
    thr.start()
    return thr


@app.route('/', methods=['GET', 'POST'])
def index():
    print(os.environ.get('MAIL_USERNAME'),os.environ.get('MAIL_PASSWORD'), os.environ.get('FLASKY_ADMIN'))
    print('xyz')
    form = NameForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.name.data).first()
        if user is None:
            user = User(username=form.name.data)
            db.session.add(user)
            session['known'] = False
            if app.config['FLASKY_ADMIN']:
                send_email(app.config['FLASKY_ADMIN'], 'New User', 'mail/new_user', user=user)
            flash('Looks like you have changed your name!')
        else:
            session['known'] = True
        session['name'] = form.name.data  # 表单中输入的名字保存在用户会话中
        form.name.data = ''
        return redirect(url_for('index'))
    return render_template(
        'index.html', current_time=datetime.utcnow(), form=form, name=session.get('name'),
        known=session.get('known', False))


@app.route('/user/<name>')
def user(name):
    return render_template('user.html', name=name)


if __name__ == '__main__':
    app.debug = True
    app.run()
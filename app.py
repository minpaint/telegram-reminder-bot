from flask import Flask

app = Flask(__name__)


@app.route('/')
def hello():
    return 'Привет! Flask работает!'


@app.route('/test')
def test():
    return 'Это тестовый маршрут'


if __name__ == '__main__':
    app.run(debug=True)

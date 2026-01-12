def greeting(name):
    """
    인사 메시지를 반환합니다.
    :param name: 인사할 사람의 이름
    :return: 인사 메시지
    """
    return f"안녕하세요, {name}님!"

if __name__ == "__main__":
    print(greeting("세계"))
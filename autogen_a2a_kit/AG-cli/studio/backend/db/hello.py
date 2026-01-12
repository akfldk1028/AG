"""Hello 모듈 - 인사말 출력 기능을 제공합니다."""


def greet(name: str = "World", greeting: str = "Hello") -> str:
    """인사말을 생성하고 출력합니다.

    Args:
        name: 인사할 대상 이름. 기본값은 "World".
        greeting: 인사말. 기본값은 "Hello".

    Returns:
        생성된 인사말 문자열.

    Examples:
        >>> greet()
        'Hello World!'
        >>> greet("Python")
        'Hello Python!'
        >>> greet("User", "Hi")
        'Hi User!'
    """
    message = f"{greeting} {name}!"
    print(message)
    return message


def main() -> None:
    """모듈 직접 실행 시 기본 인사말을 출력합니다."""
    greet()


if __name__ == "__main__":
    main()

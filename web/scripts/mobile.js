// scripts/mobile.js
console.log("init)");
// Функция для определения, является ли устройство тачскринным (без физической клавиатуры)
function isTouchDevice() {
    // Проверяем поддержку тач-событий или наличие тач-устройства
    let is_touch_device = (('ontouchstart' in window) ||
        (navigator.maxTouchPoints > 0) ||
        (navigator.msMaxTouchPoints > 0) ||
        // Для старых браузеров
        (window.DocumentTouch && document instanceof DocumentTouch) ||
        // Определяем мобильные устройства по userAgent
        /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) ||
        // Определяем по размеру экрана и возможности hover
        (window.innerWidth <= 1024 && window.matchMedia("(any-hover: none)").matches));
        console.log("IsTouchDevice: " + is_touch_device);
        return is_touch_device;
}

// Инициализация мобильных контролов
function initMobileControls() {
    // Показываем контролы только на тачскринных устройствах
    if (isTouchDevice()) {
        document.getElementById('mobile-controls').style.display = 'block';

        // Скрываем десктопные подсказки управления
        const controlsInfo = document.querySelector('.controls-info');
        if (controlsInfo) {
            controlsInfo.style.display = 'none';
        }

        // Инициализируем обработчики для мобильных контролов
        initMobileControlHandlers();
    }
}


// Инициализация обработчиков для мобильных контролов
function initMobileControlHandlers() {
    // Получаем элементы кнопок
    const upBtn = document.getElementById('btn-up');
    const leftBtn = document.getElementById('btn-left');
    const downBtn = document.getElementById('btn-down');
    const rightBtn = document.getElementById('btn-right');
    const chatBtn = document.getElementById('btn-chat');
    const tabBtn = document.getElementById('btn-tab');

    // Функция для отправки команд движения
    function sendMoveCommand(direction) {
        if (direction != null) {
            setDirection(direction);
    }
    }

    // Добавляем обработчики для кнопок движения
    function addButtonListeners(button, direction) {
        // Для сенсорных устройств
        button.addEventListener('touchstart', function(e) {
            e.preventDefault();
            this.classList.add('pressed');
            sendMoveCommand(direction);
        });

        button.addEventListener('touchend', function(e) {
            e.preventDefault();
            this.classList.remove('pressed');
        });

        button.addEventListener('touchcancel', function(e) {
            e.preventDefault();
            this.classList.remove('pressed');
        });

        // Для устройств с мышью (тестирование)
        button.addEventListener('mousedown', function() {
            this.classList.add('pressed');
            sendMoveCommand(direction);
        });

        button.addEventListener('mouseup', function() {
            this.classList.remove('pressed');
        });

        button.addEventListener('mouseleave', function() {
            this.classList.remove('pressed');
        });
    }

    // Добавляем обработчики для всех кнопок направления
    addButtonListeners(upBtn, 'up');
    addButtonListeners(leftBtn, 'left');
    addButtonListeners(downBtn, 'down');
    addButtonListeners(rightBtn, 'right');

    // Обработчики для action кнопок
    chatBtn.addEventListener('click', function() {
        // Эмулируем нажатие клавиши T для чата
        const event = new KeyboardEvent('keydown', { key: 't' });
        document.dispatchEvent(event);
    });

    tabBtn.addEventListener('click', function() {
        // Эмулируем нажатие клавиши Tab для списка игроков
        const event = new KeyboardEvent('keydown', { key: 'Tab', code: 'Tab' });
        // Предотвращаем стандартное поведение Tab
        event.preventDefault = function() {};
        document.dispatchEvent(event);
    });

    // Добавляем поддержку удерживания кнопок для непрерывного движения
    let activeInterval = null;

    function startMovement(direction) {
        // Останавливаем предыдущее движение, если есть
        if (activeInterval) {
            clearInterval(activeInterval);
        }

        // Отправляем первую команду сразу
        sendMoveCommand(direction);

        // Затем продолжаем отправлять команды с интервалом
        activeInterval = setInterval(() => {
            sendMoveCommand(direction);
        }, 150); // Интервал в мс (можно настроить)
    }

    function stopMovement() {
        if (activeInterval) {
            clearInterval(activeInterval);
            activeInterval = null;
        }
    }

    // Обновляем обработчики для поддержки удерживания
    const movementButtons = [upBtn, leftBtn, downBtn, rightBtn];
    const directions = ['up', 'left', 'down', 'right'];

    movementButtons.forEach((button, index) => {
        const direction = directions[index];

        // Обновляем обработчики для поддержки удерживания
        button.addEventListener('touchstart', function(e) {
            e.preventDefault();
            this.classList.add('pressed');
            startMovement(direction);
        });

        button.addEventListener('touchend', stopMovement);
        button.addEventListener('touchcancel', stopMovement);
        button.addEventListener('mouseleave', stopMovement);
        button.addEventListener('mouseup', stopMovement);
    });
}

// Запускаем инициализацию при полной загрузке DOM
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initMobileControls);
} else {
    initMobileControls();
}

// Также обрабатываем изменение размера окна
window.addEventListener('resize', function() {
    // При изменении размера окна проверяем, нужно ли показывать контролы
    const mobileControls = document.getElementById('mobile-controls');
    if (isTouchDevice()) {
        if (mobileControls.style.display !== 'block') {
            mobileControls.style.display = 'block';
            initMobileControlHandlers();
        }
    } else {
        mobileControls.style.display = 'none';
    }
});
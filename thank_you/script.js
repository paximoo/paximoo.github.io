students_list = [
  "Alveera Syed",
  "Abdul Kader Obri",
  "Audad Ahmed",
  "Taha Husain",
  "Vidisha Bhadviya",
  "Haider Ali",
  "Hussain Heetawala",
  "Ibrahim Vagpura",
  "Krishna Soni",
  "Kushagra Sen",
  "Parth Sharma",
  "Ruhaan Dogra",
  "Suhail Hasan",
];

const shuffle = (array) => {
  let currentIndex = array.length;

  while (currentIndex != 0) {
    let randomIndex = Math.floor(Math.random() * currentIndex);
    currentIndex--;

    [array[currentIndex], array[randomIndex]] = [
      array[randomIndex],
      array[currentIndex],
    ];
  }
};

shuffle(students_list);

const loadStudents = () => {
  students_box = document.getElementById("students-box");
  for (let i = 0; i < 13; i++) {
    new_student_box = document.createElement("div");
    new_student_box.classList.add("student");

    new_student_img = document.createElement("img");
    new_student_img.src = `media/students/${students_list[i]}.jpg`;
    new_student_box.appendChild(new_student_img);

    new_student_name = document.createElement("div");

    students_list[i].split(" ").forEach((n) => {
      new_student_first_name = document.createElement("div");
      new_student_first_name.innerHTML = n;
      new_student_name.appendChild(new_student_first_name);
    });

    new_student_box.appendChild(new_student_name);

    students_box.appendChild(new_student_box);
  }
};

document.addEventListener("DOMContentLoaded", () => {
  document
    .getElementsByClassName("animation")[0]
    .addEventListener("ended", () => {
      intro = document.getElementsByClassName("animation-container")[0];
      intro.classList.add("fade-out");

      document.getElementsByClassName("card")[0].classList.add("show");
      setTimeout(() => {
        intro.remove();
      }, 800);
    });

  loadStudents();
});

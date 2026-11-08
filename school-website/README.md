# Brightstar Primary School website

Class assignment, NOC10022 Marketing, Module 5: IMC (Friday, 6th November 2026).

Open `index.html` in a browser. There is no build step.

## What the assignment asks for, and where it is

| # | Task | Where |
|---|------|-------|
| 1 | Menu with Home, Primary 1, Primary 2, Primary 3, Primary 4, Primary 5 | Top menu on every page (`index.html`, `primary-1.html` … `primary-5.html`) |
| 2 | Student and teacher images on each page, plus a short write-up about the class and its subjects | Each `primary-N.html`: Class Teacher, About the Class, Our Subjects, Meet Our Pupils |
| 3 | All images designed in Canva at the same size and shape | `images/primary-N/` (see below) |
| 4 | Logo designed in Canva and placed on the website | `images/logo.png` (header and home page) |

## Putting in your Canva images

The images in `images/` are **placeholders**. Replace them with your own Canva designs:

1. In Canva, create a design with **Custom size 800 × 800 px** (square). Use this same size for
   every teacher and student image so they all match.
2. Design one image per person, then **Share → Download → PNG**.
3. Save each file over the placeholder with **exactly the same name**:
   - `images/primary-1/teacher.png`
   - `images/primary-1/student-1.png` … `student-6.png`
   - the same for `primary-2` up to `primary-5`
4. For the logo, create a **500 × 500 px** design, download it as **PNG with a transparent
   background**, and save it as `images/logo.png`.

The stylesheet also displays every photo as an equal square (`aspect-ratio: 1/1` with
`object-fit: cover`), so the pages stay even if one export comes out a slightly different size.

To change names, the teacher, or the class write-up, edit the text in the matching
`primary-N.html` file.

import matplotlib.pyplot as plt
import numpy as np
def main():
  # Set up the complex plane
  xmin, xmax = -2, 1
  ymin, ymax = -1.5, 1.5
  resolution = 500
  
  x = np.linspace(xmin, xmax, resolution)
  y = np.linspace(ymin, ymax, resolution)
  X, Y = np.meshgrid(x, y)
  Z = X + Y*1j
  
  # Calculate the Mandelbrot set
  c = Z.copy()
  z = np.zeros_like(Z)
  mandelbrot = np.zeros_like(Z, dtype=int)
  
  for n in range(100):
    mask = np.abs(z) <= 2
    z[mask] = z[mask]**2 + c[mask]
    mandelbrot[~mask] = n  # Store iteration count when points escape
  
  # Plot the Mandelbrot set
  plt.figure(figsize=(10, 10))
  plt.imshow(np.real(mandelbrot), extent=[xmin, xmax, ymin, ymax], cmap='hot')
  plt.colorbar(label='Iterations')
  plt.title('Mandelbrot Set')
  plt.xlabel('Re(c)')
  plt.ylabel('Im(c)')
  plt.show()

if __name__ == "__main__":
  main()

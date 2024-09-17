'use client'

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'

export function OminousMinimal() {
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 })

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      setMousePosition({ x: e.clientX, y: e.clientY })
    }

    window.addEventListener('mousemove', handleMouseMove)

    return () => {
      window.removeEventListener('mousemove', handleMouseMove)
    }
  }, [])

  return (
    <div className="min-h-screen bg-white text-gray-800 flex flex-col items-center justify-center relative overflow-hidden">
      <motion.div
        className="absolute inset-0 z-0"
        animate={{
          background: `radial-gradient(600px at ${mousePosition.x}px ${mousePosition.y}px, rgba(29, 78, 216, 0.15), transparent 80%)`,
        }}
      />
      <motion.h1
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 1, delay: 0.5 }}
        className="text-4xl md:text-6xl font-bold mb-8 tracking-wider"
      >
        Your Cooking Assistant
      </motion.h1>
      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 2, delay: 1.5 }}
        className="text-lg md:text-xl text-gray-600 mb-12"
      >
        Get cooking inspiration and guidance with our helpful app.
      </motion.p>
      <motion.div
        initial={{ scaleX: 0 }}
        animate={{ scaleX: 1 }}
        transition={{ duration: 1, delay: 2 }}
        className="w-16 h-px bg-orange-500 mb-12"
      />
      <motion.button
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        className="px-8 py-3 bg-orange-500 border border-orange-500 text-white text-sm uppercase tracking-wider hover:bg-orange-600 hover:text-white transition-colors duration-300"
      >
        Get Started
      </motion.button>
      <div className="absolute bottom-4 left-4 text-xs text-gray-600">
        © 2023 Cooking Assistant Inc.
      </div>
      <motion.div
        className="absolute top-0 left-0 w-full h-1 bg-orange-500"
        initial={{ scaleX: 0 }}
        animate={{ scaleX: 1 }}
        transition={{ duration: 2, delay: 2.5 }}
      />
      <motion.div
        className="absolute bottom-0 right-0 w-1 h-full bg-orange-500"
        initial={{ scaleY: 0 }}
        animate={{ scaleY: 1 }}
        transition={{ duration: 2, delay: 3 }}
      />
    </div>
  )
}